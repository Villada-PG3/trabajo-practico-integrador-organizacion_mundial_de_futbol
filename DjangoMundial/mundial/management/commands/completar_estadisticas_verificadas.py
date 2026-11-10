"""Completar estadísticas individuales desde fuentes externas de eventos verificables.
No altera goles/tarjetas existentes ni inventa asistencias, faltas o minutos.
Usar --simular antes de escribir.
"""
import csv
import io
import json
from collections import Counter, defaultdict
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from mundial.models import (Mundial, HistorialJugador, PartidoGrupo, PartidoEliminatoria, PartidoMundial2022,
                            EstadisticaJugadorPartido)
from mundial.management.commands.importar_eventos_grupos import normalizar

BASE26 = "https://raw.githubusercontent.com/mominullptr/FIFA-World-Cup-2026-Dataset/main/"
BASE22 = "https://raw.githubusercontent.com/statsbomb/open-data/master/data/"


def descargar(url):
    req = Request(url, headers={"User-Agent": "MundoFutbol-proyecto-educativo/1.0"})
    with urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8-sig")


def csv_remoto(nombre):
    return list(csv.DictReader(io.StringIO(descargar(BASE26 + nombre))))


def numero(campo):
    try:
        n = int(float(str(campo).strip()))
        return n if n >= 0 else None
    except (ValueError, TypeError):
        return None


def base_jugadores(mundial):
    personas = defaultdict(list)
    for h in HistorialJugador.objects.filter(mundial=mundial).select_related('jugador__seleccion'):
        jugador = h.jugador
        if jugador.seleccion_id:
            personas[(normalizar(jugador.seleccion.nombre), normalizar(jugador.apellido_nombres))].append(jugador)
    return personas


def buscar_jugador(indice, equipo, nombre):
    personas = indice.get((normalizar(equipo), normalizar(nombre)), [])
    return personas[0] if len(personas) == 1 else None


def partidos_por_pareja(mundial, historicos=False):
    modelo = PartidoMundial2022 if historicos else PartidoGrupo
    qs = modelo.objects.filter(mundial=mundial).select_related('equipo1', 'equipo2')
    if historicos:
        qs = qs.filter(fase='Grupos')
    indice = defaultdict(list)
    for p in qs:
        indice[frozenset([normalizar(p.equipo1.nombre), normalizar(p.equipo2.nombre)])].append(p)
    return indice


def eliminatorias_por_pareja(mundial):
    indice = defaultdict(list)
    for p in PartidoEliminatoria.objects.filter(mundial=mundial):
        indice[frozenset([normalizar(p.equipo1), normalizar(p.equipo2)])].append(p)
    return indice


def emparejar_eliminatoria(indice, a, b, ga, gb):
    candidatos = []
    for p in indice.get(frozenset([normalizar(a), normalizar(b)]), []):
        if ((normalizar(p.equipo1) == normalizar(a) and p.goles1 == ga and p.goles2 == gb)
                or (normalizar(p.equipo1) == normalizar(b) and p.goles1 == gb and p.goles2 == ga)):
            candidatos.append(p)
    return candidatos[0] if len(candidatos) == 1 else None


def emparejar(indice, a, b, ga, gb):
    candidatos = []
    for p in indice.get(frozenset([normalizar(a), normalizar(b)]), []):
        if ((normalizar(p.equipo1.nombre) == normalizar(a) and p.goles1 == ga and p.goles2 == gb)
                or (normalizar(p.equipo1.nombre) == normalizar(b) and p.goles1 == gb and p.goles2 == ga)):
            candidatos.append(p)
    return candidatos[0] if len(candidatos) == 1 else None


def guardar_datos(cmd, mundial, partido, jugadores, datos, simular, estadisticas):
    """Actualiza solo valores positivos verificados, sin pisar datos manuales."""
    for jugador_id, valores in datos.items():
        campo_partido = ('partido_grupo' if isinstance(partido, PartidoGrupo)
                         else 'partido_eliminatoria')
        llave = {'mundial': mundial, 'jugador_id': jugador_id, campo_partido: partido}
        existente = EstadisticaJugadorPartido.objects.filter(**llave).first()
        cambios = {}
        for campo in ('asistencias', 'faltas', 'minutos_jugados'):
            nuevo = valores.get(campo)
            if nuevo is None or nuevo <= 0:
                continue
            if existente is None or getattr(existente, campo) == 0:
                cambios[campo] = nuevo
        if not cambios:
            continue
        if existente:
            estadisticas['actualizados'] += 1
            if not simular:
                for k, v in cambios.items():
                    setattr(existente, k, v)
                existente.save(update_fields=list(cambios))
        else:
            estadisticas['creados'] += 1
            if not simular:
                EstadisticaJugadorPartido.objects.create(**llave, **cambios)
        for campo in cambios:
            estadisticas[campo] += 1


def cargar_2026(cmd, simular):
    mundial = Mundial.objects.get(anio=2026)
    indice_jugadores = base_jugadores(mundial)
    indice_partidos = partidos_por_pareja(mundial)
    indice_eliminatorias = eliminatorias_por_pareja(mundial)
    equipos = {r['team_id']: r['team_name'] for r in csv_remoto('teams.csv')}
    nombres = {r['player_id']: r['player_name'] for r in csv_remoto('squads_and_players.csv')}
    partidos = {r['match_id']: r for r in csv_remoto('matches_detailed.csv')
                if r.get('status') == 'Completed' and r.get('home_score') != '' and r.get('away_score') != ''}
    eventos = defaultdict(list)
    for e in csv_remoto('match_events.csv'):
        if e.get('match_id') in partidos and e.get('event_type') == 'Assist':
            eventos[e['match_id']].append(e)
    alineaciones = defaultdict(list)
    for e in csv_remoto('match_lineups.csv'):
        if e.get('match_id') in partidos:
            alineaciones[e['match_id']].append(e)
    resultado = Counter()
    for id_fuente, datos in partidos.items():
        ga, gb = numero(datos.get('home_score')), numero(datos.get('away_score'))
        if ga is None or gb is None:
            resultado['omitidos'] += 1
            continue
        if datos.get('stage_name') == 'Group Stage':
            partido = emparejar(indice_partidos, datos['home_team_name'], datos['away_team_name'], ga, gb)
            valido = partido is not None and partido.jugado
        else:
            partido = emparejar_eliminatoria(indice_eliminatorias, datos['home_team_name'], datos['away_team_name'], ga, gb)
            valido = partido is not None
        if not valido:
            resultado['omitidos'] += 1
            continue
        datos_jugador = defaultdict(dict)
        for e in eventos.get(id_fuente, []):
            equipo = equipos.get(e.get('team_id'), '')
            jugador = buscar_jugador(indice_jugadores, equipo, nombres.get(e.get('player_id'), ''))
            if jugador is None:
                resultado['sin_coincidencia'] += 1
                continue
            d = datos_jugador[jugador.pk]
            d['asistencias'] = d.get('asistencias', 0) + 1
        for e in alineaciones.get(id_fuente, []):
            minutos = numero(e.get('minutes_played'))
            if minutos is None or minutos == 0:
                continue
            equipo = equipos.get(e.get('team_id'), '')
            jugador = buscar_jugador(indice_jugadores, equipo, nombres.get(e.get('player_id'), ''))
            if jugador is None:
                resultado['sin_coincidencia'] += 1
                continue
            actual = datos_jugador[jugador.pk].get('minutos_jugados', 0)
            datos_jugador[jugador.pk]['minutos_jugados'] = max(actual, minutos)
        guardar_datos(cmd, mundial, partido, indice_jugadores, datos_jugador, simular, resultado)
        resultado['partidos'] += 1
    return resultado


def cargar_2022(cmd, simular):
    mundial = Mundial.objects.get(anio=2022)
    indice_jugadores = base_jugadores(mundial)
    indice_partidos = partidos_por_pareja(mundial)
    indice_eliminatorias = eliminatorias_por_pareja(mundial)
    partido_fuente = json.loads(descargar(BASE22 + 'matches/43/106.json'))
    resultado = Counter()
    for item in partido_fuente:
        ga, gb = numero(item.get('home_score')), numero(item.get('away_score'))
        a = item['home_team']['home_team_name']
        b = item['away_team']['away_team_name']
        if item.get('competition_stage', {}).get('name') == 'Group Stage':
            p = emparejar(indice_partidos, a, b, ga, gb)
        else:
            p = emparejar_eliminatoria(indice_eliminatorias, a, b, ga, gb)
        # Solo se guardan datos si hay un partido equivalente en nuestra base.
        if not p:
            resultado['omitidos'] += 1
            continue
        # Solo partidos presentes en nuestra edición con marcador cotejado.
        datos = json.loads(descargar(BASE22 + 'events/' + str(item['match_id']) + '.json'))
        filas = defaultdict(dict)
        for e in datos:
            tipo = e.get('type', {}).get('name')
            if tipo == 'Pass' and e.get('pass', {}).get('goal_assist') is True:
                columna = 'asistencias'
            elif tipo == 'Foul Committed':
                columna = 'faltas'
            else:
                continue
            jugador = buscar_jugador(indice_jugadores,
                                     e.get('team', {}).get('name'), e.get('player', {}).get('name'))
            if jugador is None:
                resultado['sin_coincidencia'] += 1
                continue
            d = filas[jugador.pk]
            d[columna] = d.get(columna, 0) + 1
        guardar_datos(cmd, mundial, p, indice_jugadores, filas, simular, resultado)
        resultado['partidos'] += 1
    return resultado


class Command(BaseCommand):
    help = 'Importa asistencias, faltas y minutos individuales verificables; no inventa datos faltantes.'

    def add_arguments(self, parser):
        parser.add_argument('--anio', type=int, choices=[2022, 2026], required=True)
        parser.add_argument('--simular', action='store_true')

    def handle(self, *args, **options):
        anio = options['anio']
        try:
            with transaction.atomic():
                if anio == 2026:
                    resultado = cargar_2026(self, options['simular'])
                else:
                    resultado = cargar_2022(self, options['simular'])
        except Mundial.DoesNotExist:
            raise CommandError(f'El Mundial {anio} no está registrado.')
        except (HTTPError, URLError, OSError, ValueError, KeyError, json.JSONDecodeError) as e:
            raise CommandError(f'No se pudo completar la importación externa: {e}') from e
        self.stdout.write(self.style.SUCCESS(
            f'{anio}: {"SIMULACIÓN" if options["simular"] else "IMPORTACIÓN"} - ' + ', '.join(f'{k}: {v}' for k,v in sorted(resultado.items()))
        ))
        self.stdout.write('Los valores no proporcionados por la fuente se conservan sin cambios. — en el panel indica que falta verificación.')