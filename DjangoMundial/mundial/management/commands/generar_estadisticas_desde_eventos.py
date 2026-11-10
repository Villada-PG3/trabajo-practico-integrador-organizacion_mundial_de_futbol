import unicodedata
from collections import Counter, defaultdict
from django.core.management.base import BaseCommand
from django.db import transaction
from mundial.models import (
    Mundial, HistorialJugador, Jugador, PartidoGrupo, PartidoEliminatoria,
    PartidoMundial2022, EventoGrupo, EventoPartido, EstadisticaJugadorPartido,
)


def normalizar(valor):
    texto = unicodedata.normalize('NFKD', str(valor or ''))
    return ' '.join(''.join(c for c in texto if not unicodedata.combining(c)).casefold().split())


class Command(BaseCommand):
    help = 'Genera estadísticas individuales verificables desde goles y tarjetas registrados.'

    def add_arguments(self, parser):
        parser.add_argument('--anio', type=int, choices=[2022, 2026], help='Importar solo una edición')
        parser.add_argument('--simular', action='store_true', help='Muestra el resultado sin escribir en la BD')

    def handle(self, *args, **opciones):
        anios = [opciones['anio']] if opciones['anio'] else [2022, 2026]
        simular = opciones['simular']
        totales = Counter()
        for anio in anios:
            mundial = Mundial.objects.filter(anio=anio).first()
            if not mundial:
                self.stdout.write(self.style.WARNING(f'{anio}: edición no encontrada'))
                continue
            # Se consideran exclusivamente jugadores inscritos en esa edición.
            historiales = HistorialJugador.objects.filter(mundial=mundial).select_related('jugador__seleccion')
            por_equipo = defaultdict(lambda: defaultdict(list))
            for historial in historiales:
                jugador = historial.jugador
                por_equipo[normalizar(jugador.seleccion.nombre)][normalizar(jugador.apellido_nombres)].append(jugador)

            partidos_grupo = list(PartidoGrupo.objects.filter(mundial=mundial).select_related('equipo1', 'equipo2'))
            partidos_elim = list(PartidoEliminatoria.objects.filter(mundial=mundial))
            por_pareja = defaultdict(list)
            for partido in partidos_grupo:
                pareja = frozenset((partido.equipo1_id, partido.equipo2_id))
                por_pareja[pareja].append(partido)

            eventos = []
            for evento in EventoGrupo.objects.filter(
                partido_grupo__mundial=mundial
            ).select_related('partido_grupo__equipo1', 'partido_grupo__equipo2'):
                p = evento.partido_grupo
                eventos.append(('grupo', p, evento))

            # Los eventos del modelo histórico de Qatar se emparejan sin inventar encuentros.
            if anio == 2022:
                historicos = EventoGrupo.objects.filter(
                    partido_qatar__mundial=mundial, partido_grupo__isnull=True
                ).select_related('partido_qatar__equipo1', 'partido_qatar__equipo2')
                for evento in historicos:
                    q = evento.partido_qatar
                    candidatos = por_pareja.get(frozenset((q.equipo1_id, q.equipo2_id)), [])
                    candidatos = [p for p in candidatos if (
                        (p.equipo1_id == q.equipo1_id and p.goles1 == q.goles1 and p.goles2 == q.goles2) or
                        (p.equipo1_id == q.equipo2_id and p.goles1 == q.goles2 and p.goles2 == q.goles1)
                    )]
                    if len(candidatos) > 1:
                        candidatos = [p for p in candidatos if p.fecha == q.fecha]
                    if len(candidatos) != 1:
                        totales['sin_partido'] += 1
                        continue
                    eventos.append(('grupo', candidatos[0], evento))

            for evento in EventoPartido.objects.filter(partido__mundial=mundial).select_related('partido'):
                eventos.append(('eliminatoria', evento.partido, evento))

            registros = defaultdict(Counter)
            for tipo_partido, partido, evento in eventos:
                tipo = (evento.tipo or '').upper()
                campo = {'GOL':'goles', 'PENAL':'goles', 'AMARILLA':'amarillas',
                         'ROJA':'rojas', 'DOBLE_AMARILLA':'rojas'}.get(tipo)
                if not campo or not evento.jugador.strip():
                    totales['sin_dato_individual'] += 1
                    continue
                equipos = ([partido.equipo1.nombre, partido.equipo2.nombre]
                           if tipo_partido == 'grupo' else [partido.equipo1, partido.equipo2])
                nombre_equipo = normalizar(evento.equipo)
                # Si el evento informa la selección, se verifica contra los participantes.
                if nombre_equipo:
                    if nombre_equipo not in {normalizar(n) for n in equipos}:
                        totales['equipo_no_coincide'] += 1
                        continue
                    equipos = [n for n in equipos if normalizar(n) == nombre_equipo]
                candidatos = []
                for equipo in equipos:
                    candidatos.extend(por_equipo[normalizar(equipo)].get(normalizar(evento.jugador), []))
                candidatos = list({j.pk: j for j in candidatos}.values())
                if len(candidatos) != 1:
                    totales['jugador_sin_coincidencia_unica'] += 1
                    continue
                jugador = candidatos[0]
                registros[(tipo_partido, partido.pk, jugador.pk)][campo] += 1
                totales['eventos_asociados'] += 1

            nuevos = []
            for (tipo_partido, partido_id, jugador_id), valores in registros.items():
                selector = ({'partido_grupo_id': partido_id} if tipo_partido == 'grupo'
                            else {'partido_eliminatoria_id': partido_id})
                # Nunca alterar registros cargados previamente a mano.
                if EstadisticaJugadorPartido.objects.filter(
                    mundial=mundial, jugador_id=jugador_id, **selector
                ).exists():
                    totales['registros_ya_existentes'] += 1
                    continue
                nuevos.append(EstadisticaJugadorPartido(
                    mundial=mundial, jugador_id=jugador_id, **selector,
                    goles=valores['goles'], amarillas=valores['amarillas'], rojas=valores['rojas']
                ))
            if not simular and nuevos:
                with transaction.atomic():
                    EstadisticaJugadorPartido.objects.bulk_create(nuevos)
            totales['registros_nuevos'] += len(nuevos)
            estado = 'SIMULACIÓN' if simular else 'CARGA'
            self.stdout.write(self.style.SUCCESS(f'{anio}: {estado} - {len(nuevos)} estadísticas individuales nuevas'))
        self.stdout.write('\nDetalle:')
        for nombre, cantidad in sorted(totales.items()):
            self.stdout.write(f'  {nombre}: {cantidad}')
        self.stdout.write('Nota: asistencias, faltas y minutos no se infieren. Sus valores 0 significan NO CARGADOS.')
