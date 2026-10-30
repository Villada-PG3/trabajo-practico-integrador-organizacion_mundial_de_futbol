"""Carga Qatar 2022 en MundoFútbol sin duplicar selecciones o jugadores.

Desde la carpeta que contiene manage.py:

  python manage.py shell < poblar_selecciones.py

Requiere conexión la primera vez para obtener los CSV públicos del repositorio

https://github.com/stiles/world-cup (datos recopilados de FIFA).

Conserva una copia local en data_qatar_2022/ para ejecuciones posteriores.

IMPORTANTE: Jugador.pasaporte se completa con un IDENTIFICADOR TÉCNICO

Q22-FIFA-<id>, no con un número real de pasaporte.

"""

import csv

import io

import unicodedata

from collections import Counter, defaultdict

from datetime import date

from pathlib import Path

from urllib.request import Request, urlopen

from django.apps import apps

from django.db import transaction

BASE = "https://raw.githubusercontent.com/stiles/world-cup/main/data/processed/2022"

CACHE = Path("data_qatar_2022")

PAISES = {

    "ARG": "Argentina", "AUS": "Australia", "BEL": "Bélgica",

    "BRA": "Brasil", "CMR": "Camerún", "CAN": "Canadá",

    "CRC": "Costa Rica", "CRO": "Croacia", "DEN": "Dinamarca",

    "ECU": "Ecuador", "ENG": "Inglaterra", "FRA": "Francia",

    "GER": "Alemania", "GHA": "Ghana", "IRN": "Irán",

    "JPN": "Japón", "KOR": "Corea del Sur", "MEX": "México",

    "MAR": "Marruecos", "NED": "Países Bajos", "POL": "Polonia",

    "POR": "Portugal", "QAT": "Qatar", "KSA": "Arabia Saudita",

    "SEN": "Senegal", "SRB": "Serbia", "ESP": "España",

    "SUI": "Suiza", "TUN": "Túnez", "USA": "Estados Unidos",

    "URU": "Uruguay", "WAL": "Gales",

}

# Entrenadores que dirigieron a las selecciones en Qatar 2022.

DIRECTORES = {

    "ARG": "Lionel Scaloni", "AUS": "Graham Arnold",

    "BEL": "Roberto Martínez", "BRA": "Tite",

    "CMR": "Rigobert Song", "CAN": "John Herdman",

    "CRC": "Luis Fernando Suárez", "CRO": "Zlatko Dalić",

    "DEN": "Kasper Hjulmand", "ECU": "Gustavo Alfaro",

    "ENG": "Gareth Southgate", "FRA": "Didier Deschamps",

    "GER": "Hansi Flick", "GHA": "Otto Addo",

    "IRN": "Carlos Queiroz", "JPN": "Hajime Moriyasu",

    "KOR": "Paulo Bento", "MEX": "Gerardo Martino",

    "MAR": "Walid Regragui", "NED": "Louis van Gaal",

    "POL": "Czesław Michniewicz", "POR": "Fernando Santos",

    "QAT": "Félix Sánchez", "KSA": "Hervé Renard",

    "SEN": "Aliou Cissé", "SRB": "Dragan Stojković",

    "ESP": "Luis Enrique", "SUI": "Murat Yakin",

    "TUN": "Jalel Kadri", "USA": "Gregg Berhalter",

    "URU": "Diego Alonso", "WAL": "Rob Page",

}

# Copas mundiales ganadas HASTA 2022, inclusive.

TITULOS = {"BRA": 5, "GER": 4, "ITA": 4, "ARG": 3, "FRA": 2,

           "URU": 2, "ENG": 1, "ESP": 1}

def canon(valor):

    return "".join(

        c for c in unicodedata.normalize("NFKD", str(valor or "").casefold())

        if not unicodedata.combining(c)

    ).strip()

def leer_csv(nombre):

    CACHE.mkdir(exist_ok=True)

    ruta = CACHE / nombre

    if ruta.exists():

        contenido = ruta.read_text(encoding="utf-8-sig")

    else:

        url = f"{BASE}/{nombre}"

        print(f"Descargando: {url}")

        req = Request(url, headers={"User-Agent": "Mozilla/5.0 MundoFutbol2022/1.0"})

        try:

            with urlopen(req, timeout=35) as r:

                contenido = r.read().decode("utf-8-sig")

        except Exception as exc:

            raise RuntimeError(

                f"No se pudo descargar {url}. Necesitás Internet en esta primera ejecución."

            ) from exc

        ruta.write_text(contenido, encoding="utf-8")

    return list(csv.DictReader(io.StringIO(contenido)))

def campos(modelo):

    return {f.name: f for f in modelo._meta.fields}

def asignar_si_existe(modelo, valores, campo, valor):

    if campo in campos(modelo):

        valores[campo] = valor

def texto_seleccion(nombre):

    # Evita crear duplicados como 'Países Bajos' y 'Holanda'.

    return canon(nombre).replace("holanda", "paises bajos")

def buscar_seleccion(modelo, nombre, mundial):

    filtro = {"mundial": mundial} if "mundial" in campos(modelo) else {}

    for obj in modelo.objects.filter(**filtro):

        if texto_seleccion(obj.nombre) == texto_seleccion(nombre):

            return obj

    return None

def elegir_choice(campo, opciones):

    """Busca un valor permitido por el modelo, comparando código y descripción."""

    if not getattr(campo, "choices", None):

        return opciones[0]

    for codigo, etiqueta in campo.flatchoices:

        if any(canon(op) in {canon(codigo), canon(etiqueta)} for op in opciones):

            return codigo

    return None

def registrar_director(modelo, seleccion, nombre, codigo):

    """Crea o reutiliza al DT con una clave técnica única y estable.

    Nunca asigna pasaportes reales ni sobrescribe los de registros manuales.

    """

    if modelo is None:

        print("AVISO: No existe PersonalTecnico; no se cargan directores técnicos.")

        return False

    fs = campos(modelo)

    if "seleccion" not in fs:

        print("AVISO: PersonalTecnico no tiene campo seleccion; se omite.")

        return False

    candidatos_nombre = ["apellido_nombres", "nombre", "nombre_completo", "nombres_apellidos", "nombres"]

    nombre_campo = next((x for x in candidatos_nombre if x in fs), None)

    if nombre_campo is None:

        print("AVISO: no se reconoce el campo de nombre de PersonalTecnico; se omite.")

        return False

    # Reusar el DT si ya está registrado en esta selección.

    existentes = list(modelo.objects.filter(seleccion=seleccion))

    existente = next(
        (x for x in existentes
         if canon(getattr(x, nombre_campo)) == canon(nombre)
         or ("apellido" in fs and
             canon(f"{getattr(x, 'nombre', '')} {getattr(x, 'apellido', '')}") == canon(nombre))),
        None,
    )

    if existente:

        return True

    valores = {"seleccion": seleccion, nombre_campo: nombre}
    if nombre_campo == "nombre" and "apellido" in fs:
        partes = nombre.rsplit(" ", 1)
        valores["nombre"] = partes[0] if len(partes) > 1 else nombre
        valores["apellido"] = partes[1] if len(partes) > 1 else "Sin apellido"

    for nombre_rol in ("cargo", "rol", "funcion", "puesto"):

        if nombre_rol in fs:

            valor = elegir_choice(

                fs[nombre_rol],

                ["DT", "Director Técnico", "Director tecnico", "Entrenador", "Head coach", "Tecnico", "Director"],

            )

            if valor is None:

                print(f"AVISO: cargo de PersonalTecnico no reconocido para {nombre}: {list(fs[nombre_rol].flatchoices)}")

                return False

            valores[nombre_rol] = valor

            break

    if "pasaporte" in fs:

        # Este valor es una clave interna inventada por el sistema,

        # NO un documento de identidad real.

        identificador = f"Q22-DT-{codigo}"

        campo = fs["pasaporte"]

        if campo.max_length is not None and len(identificador) > campo.max_length:

            raise RuntimeError(

                f"PersonalTecnico.pasaporte tiene max_length={campo.max_length}; "

                f"necesita al menos {len(identificador)} caracteres."

            )

        por_identificador = modelo.objects.filter(pasaporte=identificador).first()

        if por_identificador:

            if (por_identificador.seleccion_id == seleccion.pk

                    and canon(getattr(por_identificador, nombre_campo)) == canon(nombre)):

                return True

            raise RuntimeError(

                f"El identificador técnico {identificador} ya corresponde a otro registro. "

                "No lo sobrescribí."

            )

        valores["pasaporte"] = identificador

    try:

        modelo.objects.create(**valores)

        return True

    except Exception as exc:

        raise RuntimeError(

            f"No pude cargar el DT {nombre}. Revisá los campos obligatorios "

            f"de PersonalTecnico en models.py. Error: {exc}"

        ) from exc

def cargar():

    Mundial = apps.get_model("mundial", "Mundial")

    Seleccion = apps.get_model("mundial", "Seleccion")

    Jugador = apps.get_model("mundial", "Jugador")

    Confederacion = apps.get_model("mundial", "Confederacion")

    try:

        PersonalTecnico = apps.get_model("mundial", "PersonalTecnico")

    except LookupError:

        PersonalTecnico = None

    try:

        PartidoMundial2022 = apps.get_model("mundial", "PartidoMundial2022")

    except LookupError:

        PartidoMundial2022 = None

    mundial = Mundial.objects.filter(anio=2022).first()

    if mundial is None:

        raise RuntimeError("Primero creá el Mundial 2022 en Django Admin o con tu poblar_datos.py")

    equipos = leer_csv("teams.csv")

    jugadores = leer_csv("players.csv")

    resultados = leer_csv("results.csv")

    calendario = {r["id_match"]: r for r in leer_csv("schedule.csv")}

    if len(equipos) != 32 or len(jugadores) < 800 or len(resultados) != 64:

        raise RuntimeError(

            f"CSV incompletos: {len(equipos)} equipos, {len(jugadores)} jugadores, "

            f"{len(resultados)} partidos. No se modificó la base."

        )

    if set(PAISES) != {e["abbreviation"] for e in equipos}:

        raise RuntimeError("Los códigos de las 32 selecciones cambiaron en la fuente.")

    n_selecciones = n_jugadores = n_dt = n_partidos = 0

    mapa_selecciones = {}

    mapa_conf = {}

    jcampos = campos(Jugador)

    scampos = campos(Seleccion)

    ccampos = campos(Confederacion)

    with transaction.atomic():

        # Confederaciones y selecciones

        for e in equipos:

            codigo = e["abbreviation"]

            nombre = PAISES[codigo]

            conf_codigo = e["confederation"]

            if conf_codigo not in mapa_conf:

                opciones = ["codigo", "sigla", "abreviatura"]

                codigo_campo = next((x for x in opciones if x in ccampos), None)

                filtro = {codigo_campo: conf_codigo} if codigo_campo else {"nombre": conf_codigo}

                conf = Confederacion.objects.filter(**filtro).first()

                if conf is None:

                    val = {"nombre": conf_codigo}

                    if codigo_campo:

                        val[codigo_campo] = conf_codigo

                    conf = Confederacion.objects.create(**val)

                mapa_conf[conf_codigo] = conf

            seleccion = buscar_seleccion(Seleccion, nombre, mundial)

            if seleccion is None:

                datos = {"nombre": nombre}

                asignar_si_existe(Seleccion, datos, "mundial", mundial)

                asignar_si_existe(Seleccion, datos, "confederacion", mapa_conf[conf_codigo])

                asignar_si_existe(Seleccion, datos, "titulos", TITULOS.get(codigo, 0))

                seleccion = Seleccion.objects.create(**datos)

                n_selecciones += 1

            else:

                cambios = []

                if "confederacion" in scampos and seleccion.confederacion_id != mapa_conf[conf_codigo].pk:

                    seleccion.confederacion = mapa_conf[conf_codigo]

                    cambios.append("confederacion")

                if "mundial" in scampos and seleccion.mundial_id != mundial.pk:

                    # No reasignamos selecciones pertenecientes a otras ediciones.

                    raise RuntimeError(f"Selección {nombre} pertenece a otro Mundial.")

                if cambios:

                    seleccion.save(update_fields=cambios)

            mapa_selecciones[codigo] = seleccion

            if registrar_director(PersonalTecnico, seleccion, DIRECTORES[codigo], codigo):

                n_dt += 1

        # Plantel completo

        for j in jugadores:

            codigo = j["team_abbr"]

            seleccion = mapa_selecciones[codigo]

            fifa_id = j["player_id"].strip()

            identificador = f"Q22-FIFA-{fifa_id}"

            nombre = " ".join(j["name"].split())

            posicion = {"0": "ARQ", "1": "DEF", "2": "MED", "3": "DEL"}.get(j["position"])

            if posicion is None:

                raise RuntimeError(f"Posición FIFA desconocida para {nombre}: {j['position']}")

            numero = int(j["jersey_number"])

            nacimiento = date.fromisoformat(j["dob"])

            edad = 2022 - nacimiento.year - ((11, 20) < (nacimiento.month, nacimiento.day))

            valores = {}

            asignar_si_existe(Jugador, valores, "apellido_nombres", nombre)

            asignar_si_existe(Jugador, valores, "seleccion", seleccion)

            asignar_si_existe(Jugador, valores, "pasaporte", identificador)

            asignar_si_existe(Jugador, valores, "edad", edad)

            asignar_si_existe(Jugador, valores, "posicion", posicion)

            asignar_si_existe(Jugador, valores, "numero_camiseta", numero)

            # El CSV de FIFA usado no informa el club de 2022: NO inventarlo.

            asignar_si_existe(Jugador, valores, "equipo_actual", "No informado (Qatar 2022)")

            asignar_si_existe(Jugador, valores, "pais_equipo", "No informado")

            if "pasaporte" not in jcampos:

                raise RuntimeError("Falta Jugador.pasaporte, se necesita otra clave única")

            existente = Jugador.objects.filter(pasaporte=identificador).first()

            if existente is None:

                # Evitar duplicar por nombre+selección cuando ya se cargó manualmente.

                existente = next((x for x in Jugador.objects.filter(seleccion=seleccion)

                                 if canon(x.apellido_nombres) == canon(nombre)), None)

            if existente is None:

                Jugador.objects.create(**valores)

                n_jugadores += 1

            else:

                # Conservamos todos sus datos manuales; solo ajustamos selección si falta.

                if existente.seleccion_id != seleccion.pk:

                    raise RuntimeError(f"Jugador {nombre} tiene selección distinta: {existente.seleccion}")

        # Los 64 partidos en un modelo específico, si está creado.

        # Nunca tocar ni duplicar los PartidoEliminatoria existentes.

        if PartidoMundial2022 is not None:

            for r in resultados:

                cal = calendario[r["id_match"]]

                tipo = r["stage"]

                fase = {"First stage": "Grupos", "Round of 16": "Octavos",

                        "Quarter-final": "Cuartos", "Semi-final": "Semifinales",

                        "Play-off for third place": "Tercer puesto", "Final": "Final"}.get(tipo, tipo)

                obj, creado = PartidoMundial2022.objects.update_or_create(

                    fifa_match_id=int(r["id_match"]),

                    defaults={

                        "mundial": mundial,

                        "equipo1": mapa_selecciones[r["home_team"]],

                        "equipo2": mapa_selecciones[r["away_team"]],

                        "fecha": date.fromisoformat(r["date_utc"]),

                        "fase": fase,

                        "grupo": r["group"],

                        "goles1": int(r["home_score"]),

                        "goles2": int(r["away_score"]),

                        "penales1": int(r["home_penalties"] or 0),

                        "penales2": int(r["away_penalties"] or 0),

                        "estadio": r["stadium"],

                        "hora_local": cal["local_time"],

                    }

                )

                n_partidos += int(creado)

        else:

            print("AVISO: No existe PartidoMundial2022; los 64 partidos se descargaron "

                  "a data_qatar_2022/results.csv pero NO se guardaron en Django.")

    print("\nCarga Qatar 2022 finalizada:")

    print(f"  Selecciones nuevas: {n_selecciones} / 32")

    print(f"  Jugadores nuevos: {n_jugadores} / {len(jugadores)}")

    print(f"  Directores técnicos verificados/creados: {n_dt} / 32")

    print(f"  Partidos nuevos: {n_partidos} / 64 (si existe PartidoMundial2022)")

    print("  No se eliminaron datos existentes.")

cargar()


# ============================================================
# HISTORIAL QATAR 2022: partidos jugados, goles y asistencias
# Fuente: StatsBomb Open Data (competición 43, temporada 106).
# Se ejecuta después de cargar las selecciones y los 64 partidos.
# ============================================================

import json
from urllib.error import HTTPError, URLError

STATS_BOMB_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"

# Traduce los nombres usados por StatsBomb a los de nuestras selecciones.
ALIAS_STATSBOMB = {
    "netherlands": "paises bajos",
    "united states": "estados unidos",
    "united states of america": "estados unidos",
    "korea republic": "corea del sur",
    "south korea": "corea del sur",
    "saudi arabia": "arabia saudita",
    "iran": "iran",
    "ir iran": "iran",
    "england": "inglaterra",
    "wales": "gales",
    "spain": "espana",
    "germany": "alemania",
    "poland": "polonia",
    "croatia": "croacia",
    "france": "francia",
    "morocco": "marruecos",
    "switzerland": "suiza",
    "japan": "japon",
    "brazil": "brasil",
    "portugal": "portugal",
    "tunisia": "tunez",
    "cameroon": "camerun",
    "belgium": "belgica",
    "denmark": "dinamarca",
    "mexico": "mexico",
    "australia": "australia",
    "argentina": "argentina",
    "qatar": "qatar",
    "senegal": "senegal",
    "serbia": "serbia",
    "ecuador": "ecuador",
    "canada": "canada",
    "uruguay": "uruguay",
    "costa rica": "costa rica",
    "ghana": "ghana",
}


def equipo_statsbomb(nombre):
    nombre = canon(nombre)
    return ALIAS_STATSBOMB.get(nombre, nombre)


def consultar_statsbomb(ruta):
    url = f"{STATS_BOMB_URL}/{ruta}"
    peticion = Request(url, headers={"User-Agent": "MundoFutbol-educativo/1.0"})
    with urlopen(peticion, timeout=40) as respuesta:
        return json.load(respuesta)


def cargar_historial_qatar_2022():
    """Calcula los totales desde partidos completos, no desde la selección."""
    Mundial = apps.get_model("mundial", "Mundial")
    Seleccion = apps.get_model("mundial", "Seleccion")
    Jugador = apps.get_model("mundial", "Jugador")
    Historial = apps.get_model("mundial", "HistorialJugador")

    mundial = Mundial.objects.get(anio=2022)
    lista_partidos = consultar_statsbomb("matches/43/106.json")

    # Si la fuente está incompleta, no guardamos totales parciales.
    if len(lista_partidos) != 64:
        raise RuntimeError(
            f"StatsBomb devolvió {len(lista_partidos)} partidos (se esperaban 64). "
            "No se modificó HistorialJugador."
        )

    # Usamos el plantel original de Qatar 2022 para no atribuir estadísticas
    # a jugadores de otras ediciones con el mismo número de camiseta.
    convocados = {
        (canon(PAISES[j["team_abbr"]]), int(j["jersey_number"]), canon(j["name"]))
        for j in leer_csv("players.csv")
    }

    # Identificación estable por selección + dorsal de Qatar 2022.
    # Los dorsales fueron guardados previamente en Jugador.
    jugadores_qatar = list(
        Jugador.objects.filter(seleccion__isnull=False)
        .select_related("seleccion")
    )
    por_dorsal = defaultdict(list)
    for jugador in jugadores_qatar:
        clave = (equipo_statsbomb(jugador.seleccion.nombre), jugador.numero_camiseta)
        por_dorsal[clave].append(jugador)

    acumulados = defaultdict(Counter)
    partidos_procesados = set()

    for partido in lista_partidos:
        partido_id = partido["match_id"]
        if partido_id in partidos_procesados:
            raise RuntimeError(f"Partido duplicado en StatsBomb: {partido_id}")
        partidos_procesados.add(partido_id)

        alineaciones = consultar_statsbomb(f"lineups/{partido_id}.json")
        eventos = consultar_statsbomb(f"events/{partido_id}.json")

        if len(alineaciones) != 2:
            raise RuntimeError(f"Alineaciones incompletas del partido {partido_id}.")

        # Cada jugador queda asociado al equipo y dorsal de ese encuentro.
        identidad_por_id = {}
        equipos_del_partido = set()
        for equipo in alineaciones:
            nombre_equipo = equipo_statsbomb(equipo["team_name"])
            equipos_del_partido.add(nombre_equipo)
            for dato_jugador in equipo["lineup"]:
                identidad_por_id[dato_jugador["player_id"]] = (
                    nombre_equipo, dato_jugador["jersey_number"]
                )

        if len(equipos_del_partido) != 2:
            raise RuntimeError(f"Equipos inválidos en {partido_id}.")

        presentes = set()
        titulares_por_equipo = Counter()
        for evento in eventos:
            clase = evento.get("type", {}).get("name")
            if clase == "Starting XI":
                nombre_equipo = equipo_statsbomb(evento["team"]["name"])
                for integrante in evento.get("tactics", {}).get("lineup", []):
                    identificador = integrante["player"]["id"]
                    if identificador not in identidad_por_id:
                        raise RuntimeError(f"Titular sin dorsal en {partido_id}: {identificador}")
                    presentes.add(identidad_por_id[identificador])
                    titulares_por_equipo[nombre_equipo] += 1
            elif clase == "Substitution":
                reemplazo = evento.get("substitution", {}).get("replacement", {})
                identificador = reemplazo.get("id")
                if identificador is not None:
                    if identificador not in identidad_por_id:
                        raise RuntimeError(f"Suplente sin dorsal en {partido_id}: {identificador}")
                    presentes.add(identidad_por_id[identificador])

        if (len(titulares_por_equipo) != 2 or
                any(cantidad != 11 for cantidad in titulares_por_equipo.values())):
            raise RuntimeError(f"No se identificaron 11 titulares por equipo en {partido_id}.")

        for clave in presentes:
            acumulados[clave]["partidos_jugados"] += 1

        for evento in eventos:
            if evento.get("period") == 5:  # Tanda de penales, NO cuenta como gol.
                continue
            clase = evento.get("type", {}).get("name")
            jugador = evento.get("player", {}) or {}
            identificador = jugador.get("id")
            clave = identidad_por_id.get(identificador)
            if clave is None:
                continue
            if clase == "Shot" and evento.get("shot", {}).get("outcome", {}).get("name") == "Goal":
                acumulados[clave]["goles"] += 1
            elif clase == "Pass" and evento.get("pass", {}).get("goal_assist") is True:
                acumulados[clave]["asistencias"] += 1

        print(f"Partido {partido_id}: alineaciones y eventos procesados")

    # Solo guardamos después de haber procesado correctamente todos los partidos.
    nuevos = 0
    sin_correspondencia = []
    with transaction.atomic():
        for (equipo, dorsal), candidatos in por_dorsal.items():
            # No se asignan estadísticas si hay varios jugadores para un dorsal.
            if len(candidatos) != 1:
                continue
            jugador = candidatos[0]
            # Solo jugadores del plantel real 2022, aunque el registro
            # se hubiera creado manualmente y tenga otro pasaporte.
            if (equipo, dorsal, canon(jugador.apellido_nombres)) not in convocados:
                continue
            datos = acumulados.get((equipo, dorsal), Counter())
            obj, creado = Historial.objects.get_or_create(
                jugador=jugador,
                mundial=mundial,
                defaults={
                    "partidos_jugados": datos["partidos_jugados"],
                    "goles": datos["goles"],
                    "asistencias": datos["asistencias"],
                },
            )
            if not creado and (obj.partidos_jugados, obj.goles, obj.asistencias) == (0, 0, 0):
                # Completa un registro vacío, pero no pisa estadísticas editadas.
                obj.partidos_jugados = datos["partidos_jugados"]
                obj.goles = datos["goles"]
                obj.asistencias = datos["asistencias"]
                obj.save(update_fields=["partidos_jugados", "goles", "asistencias"])
            nuevos += int(creado)

        # Informamos si hubo jugadores con dorsal que no figura en la base,
        # sin inventar su identidad.
        for clave in acumulados:
            if len(por_dorsal.get(clave, [])) != 1:
                sin_correspondencia.append(clave)

    print(f"Historial 2022: {nuevos} registros creados. Registros ya existentes conservados.")
    if sin_correspondencia:
        print("ATENCIÓN: datos sin jugador único:", sin_correspondencia)
    print("Fuente: StatsBomb Open Data - FIFA World Cup Qatar 2022.")


# En la primera carga el programa ya ejecutó cargar() antes de llegar aquí.
# Ante una falla de conexión, no se guardan estadísticas parciales.
try:
    cargar_historial_qatar_2022()
except (HTTPError, URLError, OSError, ValueError, RuntimeError) as exc:
    print("No se completó el historial de Qatar 2022:", exc)
    print("Los jugadores y partidos cargados previamente se mantienen.")
