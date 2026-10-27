"""
Carga los partidos de eliminatorias del Mundial 2026,
incluyendo goles, tarjetas amarillas, rojas y cambios.

Fuente:
https://github.com/openfootball/worldcup.json

No genera archivos JSON ni carpetas adicionales.
No modifica los partidos de 2022.

Ejecutar:
    python manage.py shell < poblar_partidos_2026.py
"""

import json
import unicodedata
from collections import Counter
from datetime import date
from urllib.request import Request, urlopen

from django.db import transaction

from mundial.models import (
    Mundial,
    PartidoEliminatoria,
    EventoPartido,
)


# ==========================================
# FUENTE DE DATOS
# ==========================================

URL_DATOS = (
    "https://raw.githubusercontent.com/"
    "openfootball/worldcup.json/master/"
    "2026/worldcup-full.json"
)


# ==========================================
# FASES DEL MUNDIAL
# ==========================================

FASES = {
    "Round of 32": "16vos",
    "Round of 16": "Octavos",
    "Quarter-final": "Cuartos",
    "Semi-final": "Semifinal",
    "Bronze final": "Tercer Puesto",
    "Final": "Final",
}


# ==========================================
# TRADUCCIÓN DE EQUIPOS
# ==========================================

EQUIPOS = {
    "spain": "España",
    "france": "Francia",
    "england": "Inglaterra",
    "germany": "Alemania",
    "netherlands": "Países Bajos",
    "morocco": "Marruecos",
    "brazil": "Brasil",
    "japan": "Japón",
    "south africa": "Sudáfrica",
    "canada": "Canadá",
    "sweden": "Suecia",
    "norway": "Noruega",
    "mexico": "México",
    "ecuador": "Ecuador",
    "usa": "Estados Unidos",
    "united states": "Estados Unidos",
    "congo dr": "RD del Congo",
    "belgium": "Bélgica",
    "senegal": "Senegal",
    "portugal": "Portugal",
    "croatia": "Croacia",
    "switzerland": "Suiza",
    "algeria": "Argelia",
    "argentina": "Argentina",
    "cabo verde": "Cabo Verde",
    "colombia": "Colombia",
    "ghana": "Ghana",
    "australia": "Australia",
    "egypt": "Egipto",
    "paraguay": "Paraguay",
    "austria": "Austria",
    "côte d'ivoire": "Costa de Marfil",
    "bosnia and herzegovina": "Bosnia y Herzegovina",
}


def limpiar(texto):
    texto = unicodedata.normalize(
        "NFKD",
        str(texto or "")
    )

    texto = "".join(
        caracter for caracter in texto
        if not unicodedata.combining(caracter)
    )

    return " ".join(
        texto.casefold().strip().split()
    )


def traducir_equipo(nombre):
    return EQUIPOS.get(
        limpiar(nombre),
        nombre
    )


def clave_equipo(nombre):
    return limpiar(traducir_equipo(nombre))


# ==========================================
# DESCARGAR DATOS
# ==========================================

def obtener_datos():

    solicitud = Request(
        URL_DATOS,
        headers={
            "User-Agent": "MundoFutbol/1.0"
        }
    )

    with urlopen(solicitud, timeout=30) as respuesta:
        return json.load(respuesta)


# ==========================================
# RESULTADO FINAL
# ==========================================

def obtener_marcador(ficha):

    marcador = ficha["score"]

    # Si hubo tiempo extra, usar el marcador
    # después del alargue.
    goles = marcador.get(
        "et",
        marcador.get("ft")
    )

    return int(goles[0]), int(goles[1])


def obtener_info_extra(ficha):

    fecha = date.fromisoformat(
        ficha["date"]
    ).strftime("%d/%m/%Y")

    marcador = ficha["score"]

    if "p" in marcador:
        penales = marcador["p"]

        return (
            f"Penales {penales[0]}-{penales[1]}"
            f" | {fecha}"
        )

    if "et" in marcador:
        return f"Tiempo extra | {fecha}"

    return fecha


# ==========================================
# EXTRAER EVENTOS
# ==========================================

def extraer_eventos(ficha):

    equipo1 = traducir_equipo(
        ficha["team1"]
    )

    equipo2 = traducir_equipo(
        ficha["team2"]
    )

    nombres_equipos = [equipo1, equipo2]

    eventos = []

    # --------------------------------------
    # GOLES
    # --------------------------------------

    for indice, equipo in enumerate(nombres_equipos):

        clave_goles = (
            "goals1" if indice == 0
            else "goals2"
        )

        for gol in ficha.get(clave_goles, []):

            if gol.get("owngoal"):
                tipo = "AUTOGOL"

            elif gol.get("penalty"):
                tipo = "PENAL"

            else:
                tipo = "GOL"

            eventos.append({
                "tipo": tipo,
                "minuto": str(gol["minute"]),
                "equipo": equipo,
                "jugador": gol["name"],
                "jugador_entra": "",
                "jugador_sale": "",
                "descripcion": "",
            })

    # --------------------------------------
    # TARJETAS
    # --------------------------------------

    tipos_tarjeta = {
        "Y": "AMARILLA",
        "R": "ROJA",
        "Y/R": "DOBLE_AMARILLA",
    }

    for indice, tarjetas_equipo in enumerate(
        ficha.get("bookings", [])
    ):

        if indice >= len(nombres_equipos):
            continue

        equipo = nombres_equipos[indice]

        for tarjeta in tarjetas_equipo:

            tipo = tipos_tarjeta.get(
                tarjeta.get("type")
            )

            if not tipo:
                continue

            eventos.append({
                "tipo": tipo,
                "minuto": str(tarjeta["minute"]),
                "equipo": equipo,
                "jugador": tarjeta["name"],
                "jugador_entra": "",
                "jugador_sale": "",
                "descripcion": "",
            })

    # --------------------------------------
    # CAMBIOS DE JUGADORES
    # --------------------------------------

    for indice, equipo_datos in enumerate(
        ficha.get("lineup", [])
    ):

        if indice >= len(nombres_equipos):
            continue

        equipo = nombres_equipos[indice]

        for cambio in equipo_datos.get("subs", []):

            jugador_entra = cambio.get("on", "")
            jugador_sale = cambio.get("off", "")

            # No guardar cambios incompletos.
            if not jugador_entra or not jugador_sale:
                continue

            eventos.append({
                "tipo": "CAMBIO",
                "minuto": str(cambio["minute"]),
                "equipo": equipo,
                "jugador": "",
                "jugador_entra": jugador_entra,
                "jugador_sale": jugador_sale,
                "descripcion": "",
            })

    return eventos


# ==========================================
# EVITAR DUPLICADOS
# ==========================================

def firma_evento(datos):

    return (
        datos["tipo"],
        datos["minuto"],
        clave_equipo(datos["equipo"]),
        limpiar(datos["jugador"]),
        limpiar(datos["jugador_entra"]),
        limpiar(datos["jugador_sale"]),
    )


def guardar_eventos(partido, eventos):

    existentes = EventoPartido.objects.filter(
        partido=partido
    )

    firmas_existentes = {
        firma_evento({
            "tipo": evento.tipo,
            "minuto": evento.minuto,
            "equipo": evento.equipo,
            "jugador": evento.jugador,
            "jugador_entra": evento.jugador_entra,
            "jugador_sale": evento.jugador_sale,
        })
        for evento in existentes
    }

    # Si ya había goles cargados, conservarlos.
    # Así evitamos duplicar los goles importados
    # anteriormente desde otra fuente.
    hay_goles = EventoPartido.objects.filter(
        partido=partido,
        tipo__in=["GOL", "PENAL", "AUTOGOL"]
    ).exists()

    creados = Counter()

    for datos in eventos:

        if hay_goles and datos["tipo"] in (
            "GOL",
            "PENAL",
            "AUTOGOL"
        ):
            continue

        firma = firma_evento(datos)

        if firma in firmas_existentes:
            continue

        EventoPartido.objects.create(
            partido=partido,
            **datos
        )

        firmas_existentes.add(firma)
        creados[datos["tipo"]] += 1

    return creados


# ==========================================
# BUSCAR PARTIDOS EXISTENTES
# ==========================================

def buscar_partido(mundial, fase, equipo1, equipo2):

    candidatos = []

    for partido in PartidoEliminatoria.objects.filter(
        mundial=mundial,
        fase=fase
    ):

        equipos_partido = {
            clave_equipo(partido.equipo1),
            clave_equipo(partido.equipo2),
        }

        equipos_buscados = {
            clave_equipo(equipo1),
            clave_equipo(equipo2),
        }

        if equipos_partido == equipos_buscados:
            candidatos.append(partido)

    if len(candidatos) > 1:
        raise ValueError(
            f"Hay partidos duplicados: "
            f"{equipo1} vs {equipo2}"
        )

    return candidatos[0] if candidatos else None


# ==========================================
# SINCRONIZAR
# ==========================================

def sincronizar():

    mundial = Mundial.objects.filter(
        anio=2026
    ).first()

    if mundial is None:
        print(
            "ERROR: Primero tenés que cargar "
            "el Mundial 2026."
        )
        return

    try:
        datos = obtener_datos()

    except (OSError, ValueError) as error:
        print(
            "No se pudieron descargar los datos:",
            error
        )
        return

    nuevos = 0
    actualizados = 0
    omitidos = 0

    total_eventos = Counter()
    ordenes = Counter()

    for ficha in datos.get("matches", []):

        fase = FASES.get(
            ficha.get("round")
        )

        # No cargar fase de grupos.
        if not fase:
            continue

        equipo1 = traducir_equipo(
            ficha["team1"]
        )

        equipo2 = traducir_equipo(
            ficha["team2"]
        )

        goles1, goles2 = obtener_marcador(ficha)

        ordenes[fase] += 1

        partido = buscar_partido(
            mundial,
            fase,
            equipo1,
            equipo2
        )

        # Si el partido ya existe, no sobrescribir
        # resultados que puedan haber sido editados.
        if partido is not None:

            if clave_equipo(partido.equipo1) == clave_equipo(equipo1):
                resultado_local = (
                    partido.goles1,
                    partido.goles2
                )
            else:
                resultado_local = (
                    partido.goles2,
                    partido.goles1
                )

            if resultado_local != (goles1, goles2):

                print(
                    "AVISO: marcador diferente. "
                    "Se omite:",
                    equipo1,
                    equipo2
                )

                omitidos += 1
                continue

        eventos = extraer_eventos(ficha)

        # Se guarda cada partido y sus eventos
        # dentro de una transacción.
        with transaction.atomic():

            if partido is None:

                partido = PartidoEliminatoria.objects.create(
                    mundial=mundial,
                    fase=fase,
                    orden=ordenes[fase],
                    equipo1=equipo1,
                    goles1=goles1,
                    equipo2=equipo2,
                    goles2=goles2,
                    info_extra=obtener_info_extra(ficha),
                )

                nuevos += 1

            else:
                actualizados += 1

            creados = guardar_eventos(
                partido,
                eventos
            )

            total_eventos.update(creados)

        print(
            f"{fase}: {equipo1} "
            f"{goles1}-{goles2} {equipo2}"
            f" | eventos: {partido.eventos.count()}"
        )

    print("\n================================")
    print("MUNDIAL 2026 - CARGA FINALIZADA")
    print("================================")

    print("Partidos nuevos:", nuevos)
    print("Partidos existentes:", actualizados)
    print("Partidos omitidos:", omitidos)

    print("\nEVENTOS NUEVOS")

    for tipo in [
        "GOL",
        "PENAL",
        "AUTOGOL",
        "AMARILLA",
        "ROJA",
        "DOBLE_AMARILLA",
        "CAMBIO",
    ]:

        print(
            f"{tipo}: {total_eventos[tipo]}"
        )

    print(
        "\nLos datos se guardaron "
        "directamente en SQLite."
    )

    print(
        "No se creó ningún archivo adicional."
    )


# ==========================================
# EJECUTAR
# ==========================================

sincronizar()