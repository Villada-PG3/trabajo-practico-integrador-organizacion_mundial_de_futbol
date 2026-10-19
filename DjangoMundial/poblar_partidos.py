"""
Carga Qatar 2022: partidos, goles, tarjetas y cambios en la base Django.
No escribe archivos JSON. Se puede ejecutar varias veces sin duplicar eventos
idénticos. Respeta los eventos ya editados manualmente en el admin.

Ejecutar desde la carpeta de manage.py:
    python manage.py shell < poblar_partidos.py

Para importar tarjetas y cambios necesita Internet durante la ejecución,
ya que consulta los datos abiertos de StatsBomb (World Cup 2022).
Si no hay Internet, carga los goles disponibles localmente y avisa.
Datos: https://github.com/statsbomb/open-data
Licencia/atribución: StatsBomb Open Data.
"""

import json
import unicodedata
from collections import Counter
from datetime import date
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from django.apps import apps
from django.db import transaction

def gol(equipo, jugador, minuto, tipo="jugada"):
    return {"equipo": equipo, "jugador": jugador, "minuto": minuto, "tipo": tipo}


def partido(fase, fecha, hora, equipo1, goles1, equipo2, goles2, estadio,
            goles=None, penales=None):
    return {
        "fase": fase,
        "fecha": fecha,
        "hora": hora,                     # Horario local de Qatar (UTC+3)
        "equipo1": equipo1,
        "goles1": goles1,
        "equipo2": equipo2,
        "goles2": goles2,
        "estadio": estadio,
        "goles": goles or [],
        "penales": penales,               # Tanda, no se suma a goles1/goles2
    }


PARTIDOS = [
    # OCTAVOS DE FINAL (8 partidos)
    partido("Octavos", "2022-12-03", "18:00", "Países Bajos", 3, "Estados Unidos", 1,
            "Estadio Internacional Khalifa", [
                gol("Países Bajos", "Memphis Depay", "10"),
                gol("Países Bajos", "Daley Blind", "45+1"),
                gol("Estados Unidos", "Haji Wright", "76"),
                gol("Países Bajos", "Denzel Dumfries", "81"),
            ]),
    partido("Octavos", "2022-12-03", "22:00", "Argentina", 2, "Australia", 1,
            "Estadio Ahmad bin Ali", [
                gol("Argentina", "Lionel Messi", "35"),
                gol("Argentina", "Julián Álvarez", "57"),
                gol("Australia", "Enzo Fernández", "77", "autogol"),
            ]),
    partido("Octavos", "2022-12-04", "18:00", "Francia", 3, "Polonia", 1,
            "Estadio Al Thumama", [
                gol("Francia", "Olivier Giroud", "44"),
                gol("Francia", "Kylian Mbappé", "74"),
                gol("Francia", "Kylian Mbappé", "90+1"),
                gol("Polonia", "Robert Lewandowski", "90+9", "penal"),
            ]),
    partido("Octavos", "2022-12-04", "22:00", "Inglaterra", 3, "Senegal", 0,
            "Estadio Al Bayt", [
                gol("Inglaterra", "Jordan Henderson", "38"),
                gol("Inglaterra", "Harry Kane", "45+3"),
                gol("Inglaterra", "Bukayo Saka", "57"),
            ]),
    partido("Octavos", "2022-12-05", "18:00", "Japón", 1, "Croacia", 1,
            "Estadio Al Janoub", [
                gol("Japón", "Daizen Maeda", "43"),
                gol("Croacia", "Ivan Perišić", "55"),
            ], penales={"equipo1": 1, "equipo2": 3, "ganador": "Croacia"}),
    partido("Octavos", "2022-12-05", "22:00", "Brasil", 4, "Corea del Sur", 1,
            "Estadio 974", [
                gol("Brasil", "Vinícius Júnior", "7"),
                gol("Brasil", "Neymar", "13", "penal"),
                gol("Brasil", "Richarlison", "29"),
                gol("Brasil", "Lucas Paquetá", "36"),
                gol("Corea del Sur", "Paik Seung-ho", "76"),
            ]),
    partido("Octavos", "2022-12-06", "18:00", "Marruecos", 0, "España", 0,
            "Estadio Ciudad de la Educación", [],
            penales={"equipo1": 3, "equipo2": 0, "ganador": "Marruecos"}),
    partido("Octavos", "2022-12-06", "22:00", "Portugal", 6, "Suiza", 1,
            "Estadio Lusail", [
                gol("Portugal", "Gonçalo Ramos", "17"),
                gol("Portugal", "Pepe", "33"),
                gol("Portugal", "Gonçalo Ramos", "51"),
                gol("Portugal", "Raphaël Guerreiro", "55"),
                gol("Suiza", "Manuel Akanji", "58"),
                gol("Portugal", "Gonçalo Ramos", "67"),
                gol("Portugal", "Rafael Leão", "90+2"),
            ]),

    # CUARTOS DE FINAL (4 partidos)
    partido("Cuartos", "2022-12-09", "18:00", "Croacia", 1, "Brasil", 1,
            "Estadio Ciudad de la Educación", [
                gol("Brasil", "Neymar", "105+1"),
                gol("Croacia", "Bruno Petković", "117"),
            ], penales={"equipo1": 4, "equipo2": 2, "ganador": "Croacia"}),
    partido("Cuartos", "2022-12-09", "22:00", "Países Bajos", 2, "Argentina", 2,
            "Estadio Lusail", [
                gol("Argentina", "Nahuel Molina", "35"),
                gol("Argentina", "Lionel Messi", "73", "penal"),
                gol("Países Bajos", "Wout Weghorst", "83"),
                gol("Países Bajos", "Wout Weghorst", "90+11"),
            ], penales={"equipo1": 3, "equipo2": 4, "ganador": "Argentina"}),
    partido("Cuartos", "2022-12-10", "18:00", "Marruecos", 1, "Portugal", 0,
            "Estadio Al Thumama", [
                gol("Marruecos", "Youssef En-Nesyri", "42"),
            ]),
    partido("Cuartos", "2022-12-10", "22:00", "Inglaterra", 1, "Francia", 2,
            "Estadio Al Bayt", [
                gol("Francia", "Aurélien Tchouaméni", "17"),
                gol("Inglaterra", "Harry Kane", "54", "penal"),
                gol("Francia", "Olivier Giroud", "78"),
            ]),

    # SEMIFINALES (2 partidos)
    partido("Semifinal", "2022-12-13", "22:00", "Argentina", 3, "Croacia", 0,
            "Estadio Lusail", [
                gol("Argentina", "Lionel Messi", "34", "penal"),
                gol("Argentina", "Julián Álvarez", "39"),
                gol("Argentina", "Julián Álvarez", "69"),
            ]),
    partido("Semifinal", "2022-12-14", "22:00", "Francia", 2, "Marruecos", 0,
            "Estadio Al Bayt", [
                gol("Francia", "Théo Hernández", "5"),
                gol("Francia", "Randal Kolo Muani", "79"),
            ]),

    # TERCER PUESTO Y FINAL (2 partidos)
    partido("Tercer Puesto", "2022-12-17", "18:00", "Croacia", 2, "Marruecos", 1,
            "Estadio Internacional Khalifa", [
                gol("Croacia", "Joško Gvardiol", "7"),
                gol("Marruecos", "Achraf Dari", "9"),
                gol("Croacia", "Mislav Oršić", "42"),
            ]),
    partido("Final", "2022-12-18", "18:00", "Argentina", 3, "Francia", 3,
            "Estadio Lusail", [
                gol("Argentina", "Lionel Messi", "23", "penal"),
                gol("Argentina", "Ángel Di María", "36"),
                gol("Francia", "Kylian Mbappé", "80", "penal"),
                gol("Francia", "Kylian Mbappé", "81"),
                gol("Argentina", "Lionel Messi", "108"),
                gol("Francia", "Kylian Mbappé", "118", "penal"),
            ], penales={"equipo1": 4, "equipo2": 2, "ganador": "Argentina"}),
]


ALIAS_EQUIPOS = {
    "holanda": "paises bajos", "netherlands": "paises bajos",
    "paises bajos": "paises bajos", "united states": "estados unidos",
    "united states of america": "estados unidos", "usa": "estados unidos",
    "south korea": "corea del sur", "korea republic": "corea del sur",
    "morocco": "marruecos", "switzerland": "suiza",
    "england": "inglaterra", "france": "francia", "poland": "polonia",
    "japan": "japon", "croatia": "croacia", "brazil": "brasil",
    "portugal": "portugal", "argentina": "argentina",
    "australia": "australia", "spain": "espana",
    "senegal": "senegal", "cameroon": "camerun",
    "paraguay": "paraguay", "germany": "alemania",
}


def normalizar(texto):
    limpio = unicodedata.normalize("NFKD", str(texto or ""))
    limpio = "".join(c for c in limpio if not unicodedata.combining(c))
    limpio = " ".join(limpio.casefold().replace(".", "").split())
    return ALIAS_EQUIPOS.get(limpio, limpio)


def obtener_modelo(nombre):
    encontrados = [m for m in apps.get_models() if m.__name__ == nombre]
    if len(encontrados) != 1:
        raise RuntimeError(f"No se encontró el modelo {nombre}; revisá models.py y las migraciones.")
    return encontrados[0]


def verificar_goles(ficha):
    totales = Counter(normalizar(g["equipo"]) for g in ficha["goles"])
    for equipo, cantidad in [(ficha["equipo1"], ficha["goles1"]),
                              (ficha["equipo2"], ficha["goles2"])]:
        if totales[normalizar(equipo)] != cantidad:
            raise ValueError(f"Los goles del partido {ficha['equipo1']} - {ficha['equipo2']} no coinciden")


def texto_info(ficha):
    fecha = date.fromisoformat(ficha["fecha"]).strftime("%d/%m/%Y")
    if ficha["fase"] == "Tercer Puesto":
        return f"{fecha} - Tercer Puesto"
    if ficha["penales"]:
        p = ficha["penales"]
        return f"Penales {p['equipo1']}-{p['equipo2']} | {fecha}"
    return fecha


def obtener_json_web(url):
    req = Request(url, headers={"User-Agent": "MundoFutbol/1.0 (proyecto educativo)"})
    with urlopen(req, timeout=25) as respuesta:
        return json.load(respuesta)  # En memoria solamente: NO genera archivo


BASE_STATSBOMB = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"


def cargar_catalogo_statsbomb():
    try:
        return obtener_json_web(f"{BASE_STATSBOMB}/matches/43/106.json")
    except (OSError, ValueError) as error:
        print(f"AVISO: no se pudo consultar StatsBomb ({error}). Se cargarán solamente los goles.")
        return []


def encontrar_id_statsbomb(ficha, catalogo):
    deseados = {normalizar(ficha['equipo1']), normalizar(ficha['equipo2'])}
    for partido_api in catalogo:
        participantes = {
            normalizar(partido_api.get('home_team', {}).get('home_team_name')),
            normalizar(partido_api.get('away_team', {}).get('away_team_name')),
        }
        if (partido_api.get('match_date') == ficha['fecha']
                and participantes == deseados):
            return partido_api['match_id']
    return None


def minuto_visible(evento):
    # StatsBomb usa minutos transcurridos con base cero. Los sumamos 1
    # para mostrarlos como reloj futbolístico aproximado.
    m = int(evento.get('minute', 0)) + 1
    periodo = evento.get('period', 1)
    if periodo == 1 and m > 45:
        return f"45+{m - 45}"
    if periodo == 2 and m > 90:
        return f"90+{m - 90}"
    if periodo == 3 and m > 105:
        return f"105+{m - 105}"
    if periodo == 4 and m > 120:
        return f"120+{m - 120}"
    return str(m)


def evento_tarjeta(evento):
    tipo = evento.get('type', {}).get('name', '')
    info = {}
    if tipo == 'Bad Behaviour':
        info = evento.get('bad_behaviour', {})
    elif tipo == 'Foul Committed':
        info = evento.get('foul_committed', {})
    carta = info.get('card', {}).get('name', '')
    return {
        'Yellow Card': 'AMARILLA',
        'Red Card': 'ROJA',
        'Second Yellow': 'DOBLE_AMARILLA',
    }.get(carta)


def extraer_eventos_statsbomb(datos, ficha):
    nombres = {
        normalizar(ficha['equipo1']): ficha['equipo1'],
        normalizar(ficha['equipo2']): ficha['equipo2'],
    }
    extraidos = []
    vistos = set()
    for evento in datos:
        tipo = evento.get('type', {}).get('name', '')
        tarjeta = evento_tarjeta(evento)
        if tipo != 'Substitution' and not tarjeta:
            continue
        identificador = evento.get('id')
        if identificador in vistos:
            continue
        vistos.add(identificador)
        equipo_api = evento.get('team', {}).get('name', '')
        equipo = nombres.get(normalizar(equipo_api))
        if not equipo:
            continue
        minuto = minuto_visible(evento)
        jugador = evento.get('player', {}).get('name', '')
        if tarjeta:
            extraidos.append(dict(
                tipo=tarjeta, minuto=minuto, equipo=equipo,
                jugador=jugador, jugador_entra='', jugador_sale='',
                descripcion='',
            ))
        elif tipo == 'Substitution':
            cambio = evento.get('substitution', {})
            extraidos.append(dict(
                tipo='CAMBIO', minuto=minuto, equipo=equipo,
                jugador='', jugador_entra=cambio.get('replacement', {}).get('name', ''),
                jugador_sale=jugador, descripcion='',
            ))
    return extraidos


def insertar_sin_duplicar(Evento, obj, datos):
    # No se borran otros eventos existentes o editados por el usuario.
    # Se crea si no existe un registro igual en ese partido.
    _, creado = Evento.objects.get_or_create(partido=obj, **datos)
    return int(creado)


def sincronizar():
    Mundial = obtener_modelo('Mundial')
    Partido = obtener_modelo('PartidoEliminatoria')
    Evento = obtener_modelo('EventoPartido')
    mundial = Mundial.objects.get(anio=2022)
    existentes = list(Partido.objects.filter(mundial=mundial))
    usados = set()
    catalogo = cargar_catalogo_statsbomb()
    creados = actualizados = eventos_nuevos = con_fuente = 0

    for ficha in PARTIDOS:
        verificar_goles(ficha)
        equipos = {normalizar(ficha['equipo1']), normalizar(ficha['equipo2'])}
        candidatos = [p for p in existentes
                      if p.pk not in usados
                      and {normalizar(p.equipo1), normalizar(p.equipo2)} == equipos]
        if len(candidatos) > 1:
            raise RuntimeError(f"Partidos repetidos: {ficha['equipo1']} vs {ficha['equipo2']}")

        # Descargar los eventos del partido ANTES de abrir una transacción.
        adicionales = []
        match_id = encontrar_id_statsbomb(ficha, catalogo)
        if match_id:
            try:
                eventos_api = obtener_json_web(f'{BASE_STATSBOMB}/events/{match_id}.json')
                adicionales = extraer_eventos_statsbomb(eventos_api, ficha)
                con_fuente += 1
            except (OSError, ValueError) as error:
                print(f"  AVISO: tarjetas/cambios no disponibles para {ficha['equipo1']} - {ficha['equipo2']}: {error}")
        elif catalogo:
            print(f"  AVISO: partido no encontrado en StatsBomb: {ficha['equipo1']} - {ficha['equipo2']}")

        with transaction.atomic():
            if candidatos:
                obj = candidatos[0]
                mismo_orden = normalizar(obj.equipo1) == normalizar(ficha['equipo1'])
                obj.goles1 = ficha['goles1'] if mismo_orden else ficha['goles2']
                obj.goles2 = ficha['goles2'] if mismo_orden else ficha['goles1']
                if not obj.info_extra:
                    obj.info_extra = texto_info(ficha)
                # Mantener la fase original y orden de equipos ya visibles en tu web
                obj.save()
                actualizados += 1
            else:
                obj = Partido.objects.create(
                    mundial=mundial, fase=ficha['fase'],
                    equipo1=ficha['equipo1'], goles1=ficha['goles1'],
                    equipo2=ficha['equipo2'], goles2=ficha['goles2'],
                    info_extra=texto_info(ficha),
                )
                existentes.append(obj)
                creados += 1
            usados.add(obj.pk)

            for g in ficha['goles']:
                tipo = {'jugada': 'GOL', 'penal': 'PENAL', 'autogol': 'AUTOGOL'}[g['tipo']]
                datos = dict(
                    tipo=tipo, minuto=str(g['minuto']), equipo=g['equipo'],
                    jugador=g['jugador'], jugador_entra='', jugador_sale='', descripcion='',
                )
                eventos_nuevos += insertar_sin_duplicar(Evento, obj, datos)

            for datos in adicionales:
                eventos_nuevos += insertar_sin_duplicar(Evento, obj, datos)

        print(f"[{obj.pk}] {ficha['equipo1']} {ficha['goles1']}-{ficha['goles2']} {ficha['equipo2']} | eventos: {obj.eventos.count()}")

    print(f"\nFinalizado: {creados} partidos creados, {actualizados} actualizados.")
    print(f"Eventos nuevos registrados: {eventos_nuevos}.")
    print(f"Partidos con tarjetas/cambios consultados: {con_fuente}/{len(PARTIDOS)}.")
    print("No se generó ningún archivo JSON. Los eventos están en Django/admin.")
    if con_fuente < len(PARTIDOS):
        print("AVISO: las tarjetas y sustituciones podrían estar incompletas si falló Internet.")


sincronizar()
