"""Importa planteles y estadisticas del Mundial 2026 a MundoFutbol.

Desde la carpeta de manage.py, con el entorno virtual activo:
    python poblar_jugadores_2026.py --verificar
    python poblar_jugadores_2026.py --aplicar
    python poblar_jugadores_2026.py --solo-planteles --aplicar

FUENTE: repositorio stiles/world-cup, CSV derivados de las APIs de FIFA.
https://github.com/stiles/world-cup

- No modifica modelos ni crea JSON.
- Usa los identificadores FIFA empleados en la carga de Qatar 2022.
- Nunca sobrescribe historiales de 2022 ni datos personales existentes.
- Un solo commit de transaccion; si falla se revierte toda esta ejecucion.
- Si faltan estadisticas globales, se detiene antes de escribir nada.
- Para clubes no informados por FIFA, pone 'No informado' (no inventa).
"""

import argparse
import csv
import io
import os
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from django.db import transaction
from mundial.models import Mundial, Seleccion, Jugador, HistorialJugador

BASE = "https://raw.githubusercontent.com/stiles/world-cup/main/data/processed"
URL_JUGADORES = f"{BASE}/players.csv"
URL_ESTADISTICAS = f"{BASE}/player_stats.csv"

# Codigo FIFA (3 letras) -> nombre usado por la BD del proyecto
PAISES = {
    "ALG": "Argelia", "ARG": "Argentina", "AUS": "Australia",
    "AUT": "Austria", "BEL": "Bélgica", "BIH": "Bosnia y Herzegovina",
    "BRA": "Brasil", "CPV": "Cabo Verde", "CAN": "Canadá",
    "COL": "Colombia", "COD": "RD del Congo", "CRO": "Croacia",
    "CUW": "Curazao", "CZE": "República Checa", "CIV": "Costa de Marfil",
    "ECU": "Ecuador", "EGY": "Egipto", "ENG": "Inglaterra",
    "FRA": "Francia", "GER": "Alemania", "GHA": "Ghana",
    "HAI": "Haití", "IRN": "Irán", "IRQ": "Irak",
    "JPN": "Japón", "JOR": "Jordania", "KOR": "Corea del Sur",
    "MEX": "México", "MAR": "Marruecos", "NED": "Países Bajos",
    "NZL": "Nueva Zelanda", "NOR": "Noruega", "PAN": "Panamá",
    "PAR": "Paraguay", "POR": "Portugal", "QAT": "Qatar",
    "KSA": "Arabia Saudita", "SCO": "Escocia", "SEN": "Senegal",
    "RSA": "Sudáfrica", "ESP": "España", "SWE": "Suecia",
    "SUI": "Suiza", "TUN": "Túnez", "TUR": "Turquía",
    "USA": "Estados Unidos", "URU": "Uruguay", "UZB": "Uzbekistán",
}

EQUIVALENCIAS = {
    "rd congo": "rd del congo",
    "republica democratica del congo": "rd del congo",
    "congo rd": "rd del congo",
    "cote d'ivoire": "costa de marfil",
    "côte d'ivoire": "costa de marfil",
    "republica checa": "chequia",
    "czechia": "chequia",
    "curacao": "curazao",
    "holanda": "paises bajos",
    "ir iran": "iran",
}

POSICIONES = {
    "0": "ARQ", "1": "DEF", "2": "MED", "3": "DEL",
    "goalkeeper": "ARQ", "defender": "DEF",
    "midfielder": "MED", "striker": "DEL", "forward": "DEL",
}

ESTADISTICAS = {
    "partidos_jugados": ["matches_played", "appearances", "matches", "games_played", "match_appearances", "total_matches_played", "played"],
    "goles": ["goals", "goals_scored", "total_goals", "goal_scored"],
    "asistencias": ["assists", "goal_assists", "total_assists", "goal_assist"],
}


def canon(texto):
    texto = unicodedata.normalize("NFD", str(texto or ""))
    texto = "".join(x for x in texto if unicodedata.category(x) != "Mn")
    texto = " ".join(texto.casefold().strip().split())
    return EQUIVALENCIAS.get(texto, texto)


def csv_remoto(url):
    print("Descargando:", url)
    solicitud = Request(url, headers={"User-Agent": "MundoFutbol-Django/1.0"})
    try:
        with urlopen(solicitud, timeout=50) as respuesta:
            datos = respuesta.read().decode("utf-8-sig")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError("No se pudo descargar la fuente. Verificá Internet o la URL: " + url) from exc
    lector = csv.DictReader(io.StringIO(datos))
    filas = list(lector)
    if not filas:
        raise RuntimeError("La fuente está vacía: " + url)
    print("Filas descargadas:", len(filas))
    return filas


def numero(valor, etiqueta):
    valor = str(valor or "").strip()
    if not valor:
        raise ValueError("Falta un número requerido: " + etiqueta)
    try:
        flotante = float(valor)
    except ValueError as exc:
        raise ValueError(f"Dato no numérico para {etiqueta}: {valor!r}") from exc
    if flotante < 0 or not flotante.is_integer():
        raise ValueError(f"Dato no válido para {etiqueta}: {valor!r}")
    return int(flotante)


def cargar_estadisticas(filas):
    columnas = set(filas[0])
    if not {"player_id", "stat", "value"}.issubset(columnas):
        raise RuntimeError("Cambió el formato de player_stats.csv. Columnas: " + str(sorted(columnas)))
    claves = {str(f["stat"]).strip().lower() for f in filas}
    elegidas = {}
    for campo, variantes in ESTADISTICAS.items():
        elegidas[campo] = next((v for v in variantes if v in claves), None)
    print("Estadísticas encontradas:", elegidas)
    if any(v is None for v in elegidas.values()):
        print("Nombres de estadísticas disponibles (primeras 100):", sorted(claves)[:100])
        raise RuntimeError("Falta reconocer alguna métrica de FIFA. No se importó nada. Revisá la lista anterior.")
    por_jugador = defaultdict(dict)
    for fila in filas:
        fifa_id = str(fila["player_id"]).strip()
        stat = str(fila["stat"]).strip().lower()
        if stat in elegidas.values():
            por_jugador[fifa_id][stat] = numero(fila["value"], f"{fifa_id}/{stat}")
    return {
        fifa_id: {campo: datos.get(stat, 0) for campo, stat in elegidas.items()}
        for fifa_id, datos in por_jugador.items()
    }


def preparar_jugadores(filas):
    esperadas = {"player_id", "name", "team_abbr", "position", "jersey_number", "dob"}
    if not esperadas.issubset(filas[0]):
        raise RuntimeError("Cambió players.csv; faltan columnas: " + str(esperadas - set(filas[0])))
    jugadores = []
    ids = set()
    equipos = Counter()
    for fila in filas:
        equipo = fila["team_abbr"].strip().upper()
        if equipo not in PAISES:
            raise RuntimeError(f"País FIFA desconocido {equipo!r}. No se importó nada.")
        identificador = fila["player_id"].strip()
        nombre = " ".join(fila["name"].strip().split())
        if not identificador or not nombre or identificador in ids:
            raise RuntimeError(f"Jugador sin ID/nombre o repetido: {identificador!r}")
        ids.add(identificador)
        pos = POSICIONES.get(fila["position"].strip().lower())
        if pos is None:
            raise RuntimeError(f"Posición desconocida de {nombre}: {fila['position']!r}")
        dorsal = numero(fila["jersey_number"], "dorsal de " + nombre)
        if not (1 <= dorsal <= 99):
            raise RuntimeError(f"Dorsal fuera de rango: {nombre}: {dorsal}")
        nacimiento = date.fromisoformat(fila["dob"][:10])
        edad = 2026 - nacimiento.year - ((6, 11) < (nacimiento.month, nacimiento.day))
        if not (15 <= edad <= 50):
            raise RuntimeError(f"Edad fuera de rango: {nombre}: {edad}")
        jugadores.append({
            "fifa_id": identificador, "nombre": nombre, "pais": PAISES[equipo],
            "posicion": pos, "numero": dorsal, "edad": edad,
        })
        equipos[equipo] += 1
    if len(equipos) != 48:
        raise RuntimeError(f"Esperaba 48 selecciones, pero el CSV contiene {len(equipos)}. No se importó nada.")
    print(f"Planteles: {len(jugadores)} jugadores en {len(equipos)} selecciones.")
    return jugadores


def ejecutar(aplicar=False, solo_planteles=False):
    # Descargas y validación COMPLETAS antes de comenzar a escribir en SQLite.
    filas = csv_remoto(URL_JUGADORES)
    lista = preparar_jugadores(filas)
    stats = {}
    if not solo_planteles:
        stats = cargar_estadisticas(csv_remoto(URL_ESTADISTICAS))
        sin_stats = [j["fifa_id"] for j in lista if j["fifa_id"] not in stats]
        print("Jugadores sin filas estadísticas (se consideran 0):", len(sin_stats))
    mundial = Mundial.objects.filter(anio=2026).first()
    if mundial is None:
        raise RuntimeError("No existe Mundial 2026. Ejecutá primero tu poblar_datos.py.")
    existentes = list(Seleccion.objects.all())
    mapa = {}
    for nombre in set(j["pais"] for j in lista):
        coincidencias = [s for s in existentes if canon(s.nombre) == canon(nombre)]
        if len(coincidencias) != 1:
            raise RuntimeError(f"Esperaba una selección registrada para {nombre}: encontré {len(coincidencias)}. Revisa duplicados.")
        mapa[canon(nombre)] = coincidencias[0]

    creados = 0
    nuevos_historiales = 0
    actualizados_historiales = 0
    reusados = 0
    # Se verifica tambien que no haya fichas duplicadas por nombre entre compañeros.
    with transaction.atomic():
        for j in lista:
            seleccion = mapa[canon(j["pais"])]
            id2022 = "Q22-FIFA-" + j["fifa_id"]
            id2026 = "Q26-FIFA-" + j["fifa_id"]
            jugador = Jugador.objects.filter(pasaporte__in=[id2022, id2026]).first()
            if jugador is not None and jugador.seleccion_id != seleccion.pk:
                raise RuntimeError(f"El ID FIFA de {j['nombre']} está asociado a otra selección. No se modificó nada.")
            if jugador is None:
                coincidencias = [p for p in Jugador.objects.filter(seleccion=seleccion)
                                 if canon(p.apellido_nombres) == canon(j["nombre"])]
                if len(coincidencias) > 1:
                    raise RuntimeError(f"Fichas duplicadas para {j['nombre']} ({seleccion.nombre}). Abortado.")
                jugador = coincidencias[0] if coincidencias else None
            if jugador is None:
                jugador = Jugador.objects.create(
                    apellido_nombres=j["nombre"], pasaporte=id2026,
                    edad=j["edad"], posicion=j["posicion"],
                    numero_camiseta=j["numero"], seleccion=seleccion,
                    equipo_actual="No informado", pais_equipo="No informado",
                )
                creados += 1
            else:
                reusados += 1
                # No se sobrescriben datos de 2022 ni cambios manuales.
                # Tampoco hay pasaporte real en la fuente: IDs técnicos.
            if not solo_planteles:
                valores = stats.get(j["fifa_id"], {
                    "partidos_jugados": 0, "goles": 0, "asistencias": 0,
                })
                _, creado = HistorialJugador.objects.update_or_create(
                    jugador=jugador, mundial=mundial, defaults=valores
                )
                if creado:
                    nuevos_historiales += 1
                else:
                    actualizados_historiales += 1
        if not aplicar:
            transaction.set_rollback(True)
            print("MODO VERIFICACIÓN: cambios revertidos, base de datos intacta.")
        else:
            print("IMPORTACIÓN GUARDADA en SQLite.")
    print("Jugadores nuevos:", creados)
    print("Jugadores existentes reutilizados:", reusados)
    if solo_planteles:
        print("No se modificó HistorialJugador (modo solo planteles).")
    else:
        print("Historiales 2026 nuevos:", nuevos_historiales)
        print("Historiales 2026 actualizados:", actualizados_historiales)
    print("No se tocaron historiales de otras ediciones.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Importar jugadores y estadísticas FIFA Mundial 2026")
    modos = parser.add_mutually_exclusive_group()
    modos.add_argument("--verificar", action="store_true", help="Simula la carga sin guardar cambios")
    modos.add_argument("--aplicar", action="store_true", help="Guarda los cambios en SQLite")
    parser.add_argument("--solo-planteles", action="store_true", help="Importar planteles sin estadísticas")
    args = parser.parse_args()
    try:
        ejecutar(aplicar=args.aplicar, solo_planteles=args.solo_planteles)
    except Exception as exc:
        print("ERROR:", exc, file=sys.stderr)
        sys.exit(1)
