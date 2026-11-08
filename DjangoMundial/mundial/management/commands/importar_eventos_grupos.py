"""Importa eventos de 2022 (StatsBomb Open Data) y 2026 (dataset comunitario).
Uso: python manage.py importar_eventos_grupos --anio 2022 --simular
     python manage.py importar_eventos_grupos --anio 2022
     python manage.py importar_eventos_grupos --anio 2026
Sólo importa encuentros con equipos y marcador verificados. No borra ni reemplaza eventos.
"""
import csv
import io
import json
import re
import unicodedata
from collections import Counter, defaultdict
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from mundial.models import Mundial, PartidoGrupo, PartidoMundial2022, EventoGrupo

SB = "https://raw.githubusercontent.com/statsbomb/open-data/master/data/"
WC26 = "https://raw.githubusercontent.com/mominullptr/FIFA-World-Cup-2026-Dataset/main/"


def obtener(url):
    with urlopen(Request(url, headers={"User-Agent": "MundoFutbol-educativo/1.0"}), timeout=35) as respuesta:
        return respuesta.read().decode("utf-8-sig")


def normalizar(s):
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]", "", s.lower())
    aliases = {
        "usa": "estadosunidos", "unitedstates": "estadosunidos", "unitedstatesofamerica": "estadosunidos",
        "southkorea": "coreadelsur", "korearepublic": "coreadelsur", "republicofkorea": "coreadelsur",
        "iriran": "iran", "iranislamicrepublic": "iran", "iriran": "iran",
        "saudiarabia": "arabiasaudita", "saudiarabia": "arabiasaudita",
        "netherlands": "paisesbajos", "the netherlands": "paisesbajos",
        "czechia": "chequia", "czechrepublic": "chequia", "republicacheca": "chequia",
        "morocco": "marruecos", "germany": "alemania", "brazil": "brasil", "japan": "japon",
        "france": "francia", "sweden": "suecia", "cotedivoire": "costademarfil",
        "norway": "noruega", "mexico": "mexico", "ecuador": "ecuador", "england": "inglaterra",
        "congodr": "rddelcongo", "drcongo": "rddelcongo", "rdcongo": "rddelcongo",
        "republicademocraticadelcongo": "rddelcongo", "belgium": "belgica",
        "senegal": "senegal", "portugal": "portugal", "croatia": "croacia", "spain": "espana",
        "austria": "austria", "switzerland": "suiza", "algeria": "argelia",
        "argentina": "argentina", "capeverde": "caboverde", "caboverde": "caboverde",
        "colombia": "colombia", "ghana": "ghana", "australia": "australia",
        "egypt": "egipto", "bosniaandherzegovina": "bosniayherzegovina",
        "qatar": "qatar", "poland": "polonia", "denmark": "dinamarca", "tunisia": "tunez",
        "wales": "gales", "uruguay": "uruguay", "cameroon": "camerun",
        "serbia": "serbia", "switzerland": "suiza", "canada": "canada",
        "costarica": "costarica", "japan": "japon", "germany": "alemania",
        "portugal": "portugal", "southafrica": "sudafrica", "newzealand": "nuevazelanda",
        "turkiye": "turquia", "turkey": "turquia", "ivorycoast": "costademarfil",
        "haiti": "haiti", "scotland": "escocia", "iraq": "irak",
        "uzbekistan": "uzbekistan", "jordan": "jordania", "panama": "panama"
    }
    return aliases.get(s, s)


def buscar_partido(mundial, equipo1, equipo2, g1, g2, qatar=False):
    Modelo = PartidoMundial2022 if qatar else PartidoGrupo
    candidatos = Modelo.objects.filter(mundial=mundial).select_related("equipo1", "equipo2")
    if qatar:
        candidatos = candidatos.filter(fase="Grupos")
    else:
        candidatos = candidatos.filter(jugado=True)
    iguales = []
    for p in candidatos:
        if normalizar(p.equipo1.nombre) == normalizar(equipo1) and normalizar(p.equipo2.nombre) == normalizar(equipo2) and p.goles1 == g1 and p.goles2 == g2:
            iguales.append(p)
        elif normalizar(p.equipo1.nombre) == normalizar(equipo2) and normalizar(p.equipo2.nombre) == normalizar(equipo1) and p.goles1 == g2 and p.goles2 == g1:
            iguales.append(p)
    return iguales[0] if len(iguales) == 1 else None


def importar_2022(cmd, simular):
    mundial = Mundial.objects.get(anio=2022)
    partidos_fuente = json.loads(obtener(SB + "matches/43/106.json"))
    creados = omitidos = procesados = 0
    for dato in partidos_fuente:
        if dato.get("competition_stage", {}).get("name") != "Group Stage":
            continue
        local = dato["home_team"]["home_team_name"]
        visita = dato["away_team"]["away_team_name"]
        partido = buscar_partido(mundial, local, visita, dato["home_score"], dato["away_score"], qatar=True)
        if partido is None:
            omitidos += 1
            cmd.stdout.write(cmd.style.WARNING(f"2022 sin coincidencia única: {local} vs {visita}"))
            continue
        datos = json.loads(obtener(SB + f"events/{dato['match_id']}.json"))
        procesados += 1
        with transaction.atomic():
            for evento in datos:
                tipo_src = evento.get("type", {}).get("name", "")
                tipo = None
                if tipo_src == "Shot" and evento.get("shot", {}).get("outcome", {}).get("name") == "Goal":
                    tipo = "PENAL" if evento.get("shot", {}).get("type", {}).get("name") == "Penalty" else "GOL"
                elif tipo_src == "Own Goal Against":
                    tipo = "AUTOGOL"
                elif tipo_src == "Substitution":
                    tipo = "CAMBIO"
                elif tipo_src == "Bad Behaviour":
                    card = evento.get("bad_behaviour", {}).get("card", {}).get("name", "")
                    tipo = {"Yellow Card": "AMARILLA", "Red Card": "ROJA", "Second Yellow": "DOBLE_AMARILLA"}.get(card)
                elif tipo_src == "Foul Committed":
                    card = evento.get("foul_committed", {}).get("card", {}).get("name", "")
                    tipo = {"Yellow Card": "AMARILLA", "Red Card": "ROJA", "Second Yellow": "DOBLE_AMARILLA"}.get(card)
                    # No guardamos cada falta en el timeline: sería demasiado extenso.
                if not tipo:
                    continue
                minuto = str(evento.get("minute", 0))
                jugador = evento.get("player", {}).get("name", "")
                equipo = evento.get("team", {}).get("name", "")
                replacement = evento.get("substitution", {}).get("replacement", {}).get("name", "")
                # Identificador de fuente para que la importación sea idempotente.
                referencia = "StatsBomb id=" + str(evento["id"])
                if not simular:
                    _, fue_creado = EventoGrupo.objects.get_or_create(
                        partido_qatar=partido, descripcion=referencia,
                        defaults={"tipo": tipo, "minuto": minuto, "jugador": jugador, "equipo": equipo,
                                  "jugador_sale": jugador if tipo == "CAMBIO" else "",
                                  "jugador_entra": replacement if tipo == "CAMBIO" else ""},
                    )
                    creados += int(fue_creado)
                else:
                    creados += 1
        cmd.stdout.write(f"2022: {local} vs {visita} — eventos revisados: {len(datos)}")
    return procesados, creados, omitidos


def importar_2026(cmd, simular):
    mundial = Mundial.objects.get(anio=2026)
    def csv_f(archivo):
        return list(csv.DictReader(io.StringIO(obtener(WC26 + archivo))))
    equipos = {r["team_id"]: r["team_name"] for r in csv_f("teams.csv")}
    jugadores = {r["player_id"]: r["player_name"] for r in csv_f("squads_and_players.csv")}
    partidos = csv_f("matches_detailed.csv")
    eventos = defaultdict(list)
    for r in csv_f("match_events.csv"):
        eventos[r["match_id"]].append(r)
    # Las estadísticas de equipo son opcionales: si la fuente no las publica,
    # se conservan intactos los valores existentes.
    estadisticas = defaultdict(dict)
    try:
        for fila in csv_f("match_team_stats.csv"):
            estadisticas[fila["match_id"]][normalizar(equipos.get(fila["team_id"], ""))] = fila
    except (URLError, OSError, ValueError, KeyError):
        pass
    procesados = creados = omitidos = 0
    for dato in partidos:
        if dato.get("stage_name") != "Group Stage":
            continue
        if not dato.get("home_score") or not dato.get("away_score"):
            # Para 0 goles, CSV suele contener '0'. Si está vacío es pendiente.
            omitidos += 1
            continue
        a, b = dato["home_team_name"], dato["away_team_name"]
        partido = buscar_partido(mundial, a, b, int(dato["home_score"]), int(dato["away_score"]))
        if partido is None:
            omitidos += 1
            cmd.stdout.write(cmd.style.WARNING(f"2026 sin coincidencia única: {a} vs {b}"))
            continue
        lista = eventos.get(dato["match_id"], [])
        # Validación estricta: fuente de goles debe coincidir con marcador.
        goles_fuente = Counter()
        for e in lista:
            if e.get("event_type") not in ("Goal", "Own Goal"):
                continue
            equipo = normalizar(equipos.get(e["team_id"], ""))
            if e["event_type"] == "Own Goal":
                otros = {normalizar(a), normalizar(b)} - {equipo}
                if len(otros) != 1:
                    continue
                equipo = otros.pop()
            goles_fuente[equipo] += 1
        # Si hay al menos eventos de goles, deben cuadrar con el marcador.
        esperados = Counter({normalizar(a): int(dato["home_score"]), normalizar(b): int(dato["away_score"])})
        if goles_fuente != esperados:
            omitidos += 1
            cmd.stdout.write(cmd.style.WARNING(f"2026 goles no coinciden: {a} vs {b}, se omite"))
            continue
        procesados += 1
        with transaction.atomic():
            # Completar córners y faltas cuando la fuente los proporciona.
            # No sobrescribir datos que alguien ya cargó manualmente.
            columnas = {"corners": "corners", "fouls": "faltas"}
            cambios = []
            for equipo_nombre, lado in ((a, "1" if normalizar(partido.equipo1.nombre) == normalizar(a) else "2"),
                                        (b, "1" if normalizar(partido.equipo1.nombre) == normalizar(b) else "2")):
                fila = estadisticas.get(dato["match_id"], {}).get(normalizar(equipo_nombre), {})
                for columna, campo in columnas.items():
                    valor = fila.get(columna, "")
                    atributo = f"{campo}{lado}"
                    if valor not in ("", None) and getattr(partido, atributo) == 0:
                        try:
                            nuevo = int(float(valor))
                        except (ValueError, TypeError):
                            continue
                        if nuevo >= 0 and not simular:
                            setattr(partido, atributo, nuevo)
                            cambios.append(atributo)
            if cambios:
                partido.save(update_fields=cambios)
            for e in lista:
                tipo = {"Goal": "GOL", "Own Goal": "AUTOGOL", "Yellow Card": "AMARILLA", "Red Card": "ROJA", "Second Yellow": "DOBLE_AMARILLA"}.get(e.get("event_type"))
                if tipo is None:
                    continue
                referencia = "WC26 id=" + str(e["event_id"])
                if not simular:
                    _, fue_creado = EventoGrupo.objects.get_or_create(
                        partido_grupo=partido, descripcion=referencia,
                        defaults={"tipo": tipo, "minuto": str(e["minute"]),
                                  "equipo": equipos.get(e["team_id"], ""),
                                  "jugador": jugadores.get(e["player_id"], "Sin identificar")},
                    )
                    creados += int(fue_creado)
                else:
                    creados += 1
        cmd.stdout.write(f"2026: {a} vs {b} — eventos disponibles: {len(lista)}")
    return procesados, creados, omitidos


class Command(BaseCommand):
    help = "Importar goles, tarjetas y cambios de la fase de grupos con fuentes verificables."

    def add_arguments(self, parser):
        parser.add_argument("--anio", type=int, choices=[2022, 2026], required=True)
        parser.add_argument("--simular", action="store_true")

    def handle(self, *args, **opts):
        anio, simular = opts["anio"], opts["simular"]
        try:
            with transaction.atomic():
                if anio == 2022:
                    procesados, creados, omitidos = importar_2022(self, simular)
                else:
                    procesados, creados, omitidos = importar_2026(self, simular)
        except Mundial.DoesNotExist:
            raise CommandError(f"El Mundial {anio} no existe en la base de datos.")
        except (URLError, HTTPError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            raise CommandError(f"No se pudieron leer o validar los datos externos: {exc}") from exc
        self.stdout.write(self.style.SUCCESS(f"{anio}: partidos coincidentes={procesados}, eventos {'estimados' if simular else 'nuevos'}={creados}, omitidos={omitidos}"))
        if anio == 2026:
            self.stdout.write("La fuente 2026 no incluye sustituciones en match_events.csv; pueden añadirse manualmente desde el panel.")
