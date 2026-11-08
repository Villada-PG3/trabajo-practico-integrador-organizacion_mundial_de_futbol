"""Carga los 48 partidos de grupos de 2022 y los 72 de 2026.
Fuente de los resultados 2026: FIFA, calendario/resultados oficiales.
Los registros 2022 se copian desde PartidoMundial2022 (ya cargado).
Uso: python manage.py cargar_grupos_2022_2026 --simular
     python manage.py cargar_grupos_2022_2026
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from mundial.models import Mundial, Seleccion, PosicionGrupo, PartidoGrupo, PartidoMundial2022

# Grupo: (equipo 1, goles 1, equipo 2, goles 2).
# Se usa el nombre que figura en la tabla mundial_seleccion.
RESULTADOS_2026 = {
    'A': [('México',2,'Sudáfrica',0),('Corea del Sur',2,'Chequia',1),('Chequia',1,'Sudáfrica',1),('México',1,'Corea del Sur',0),('Chequia',0,'México',3),('Sudáfrica',1,'Corea del Sur',0)],
    'B': [('Canadá',1,'Bosnia y Herzegovina',1),('Qatar',1,'Suiza',1),('Suiza',4,'Bosnia y Herzegovina',1),('Canadá',6,'Qatar',0),('Suiza',2,'Canadá',1),('Bosnia y Herzegovina',3,'Qatar',1)],
    'C': [('Haití',0,'Escocia',1),('Brasil',1,'Marruecos',1),('Brasil',3,'Haití',0),('Escocia',0,'Marruecos',1),('Marruecos',4,'Haití',2),('Escocia',0,'Brasil',3)],
    'D': [('Estados Unidos',4,'Paraguay',1),('Australia',2,'Turquía',0),('Turquía',0,'Paraguay',1),('Estados Unidos',2,'Australia',0),('Turquía',3,'Estados Unidos',2),('Paraguay',0,'Australia',0)],
    'E': [('Costa de Marfil',1,'Ecuador',0),('Alemania',7,'Curazao',1),('Alemania',2,'Costa de Marfil',1),('Ecuador',0,'Curazao',0),('Curazao',0,'Costa de Marfil',2),('Ecuador',2,'Alemania',1)],
    'F': [('Países Bajos',2,'Japón',2),('Suecia',5,'Túnez',1),('Países Bajos',5,'Suecia',1),('Túnez',0,'Japón',4),('Japón',1,'Suecia',1),('Túnez',1,'Países Bajos',3)],
    'G': [('Irán',2,'Nueva Zelanda',2),('Bélgica',1,'Egipto',1),('Bélgica',0,'Irán',0),('Nueva Zelanda',1,'Egipto',3),('Egipto',1,'Irán',1),('Nueva Zelanda',1,'Bélgica',5)],
    'H': [('Arabia Saudita',1,'Uruguay',1),('España',0,'Cabo Verde',0),('Uruguay',2,'Cabo Verde',2),('España',4,'Arabia Saudita',0),('Cabo Verde',0,'Arabia Saudita',0),('Uruguay',0,'España',1)],
    'I': [('Francia',3,'Senegal',1),('Irak',1,'Noruega',4),('Noruega',3,'Senegal',2),('Francia',3,'Irak',0),('Noruega',1,'Francia',4),('Senegal',5,'Irak',0)],
    'J': [('Argentina',3,'Argelia',0),('Austria',3,'Jordania',1),('Argentina',2,'Austria',0),('Jordania',1,'Argelia',2),('Argelia',3,'Austria',3),('Jordania',1,'Argentina',3)],
    'K': [('Portugal',1,'RD del Congo',1),('Uzbekistán',1,'Colombia',3),('Portugal',5,'Uzbekistán',0),('Colombia',1,'RD del Congo',0),('Colombia',0,'Portugal',0),('RD del Congo',3,'Uzbekistán',1)],
    'L': [('Ghana',1,'Panamá',0),('Inglaterra',4,'Croacia',2),('Inglaterra',0,'Ghana',0),('Panamá',0,'Croacia',1),('Panamá',0,'Inglaterra',2),('Croacia',2,'Ghana',1)],
}
# Sólo aliases entre PosicionGrupo.equipo y Seleccion.nombre.
ALIAS_GRUPOS = {'República Checa': 'Chequia', 'RD Congo': 'RD del Congo'}

class Command(BaseCommand):
    help = 'Carga partidos de grupos reales 2022 y 2026 sin duplicar registros.'

    def add_arguments(self, parser):
        parser.add_argument('--simular', action='store_true', help='Ver lo que se haría sin modificar la BD.')

    def handle(self, *args, **opciones):
        simular = opciones['simular']
        try:
            qatar = Mundial.objects.get(anio=2022)
            mundial26 = Mundial.objects.get(anio=2026)
        except (Mundial.DoesNotExist, Mundial.MultipleObjectsReturned) as exc:
            raise CommandError(f'Deben existir exactamente los Mundiales 2022 y 2026: {exc}') from exc

        selecciones = {s.nombre: s for s in Seleccion.objects.all()}
        grupos26 = {}
        for posicion in PosicionGrupo.objects.filter(mundial=mundial26):
            nombre = ALIAS_GRUPOS.get(posicion.equipo, posicion.equipo)
            grupos26.setdefault(posicion.grupo, set()).add(nombre)
        grupos22 = {}
        for posicion in PosicionGrupo.objects.filter(mundial=qatar):
            nombre = ALIAS_GRUPOS.get(posicion.equipo, posicion.equipo)
            grupos22.setdefault(posicion.grupo, set()).add(nombre)

        # Validaciones ANTES de efectuar escrituras.
        historicos = list(PartidoMundial2022.objects.filter(mundial=qatar, fase='Grupos').select_related('equipo1', 'equipo2'))
        if len(historicos) != 48:
            raise CommandError(f'Se esperaban 48 partidos de grupos históricos de Qatar; encontrados: {len(historicos)}. No se modificó nada.')
        if len(RESULTADOS_2026) != 12 or sum(map(len, RESULTADOS_2026.values())) != 72:
            raise CommandError('El catálogo 2026 debe tener 72 partidos en 12 grupos.')
        for letra, partidos in RESULTADOS_2026.items():
            grupo = f'Grupo {letra}'
            if len(partidos) != 6:
                raise CommandError(f'{grupo}: cantidad incorrecta de encuentros.')
            presentes = grupos26.get(grupo, set())
            if len(presentes) != 4:
                raise CommandError(f'{grupo}: esperadas 4 selecciones, hay {presentes}.')
            cruces = set()
            for a, _, b, _ in partidos:
                if a not in presentes or b not in presentes or a not in selecciones or b not in selecciones:
                    raise CommandError(f'{grupo}: selección no encontrada o fuera de su grupo: {a} - {b}.')
                llave = frozenset((a, b))
                if len(llave) != 2 or llave in cruces:
                    raise CommandError(f'{grupo}: cruce duplicado o inválido: {a} - {b}.')
                cruces.add(llave)
        for p in historicos:
            grupo = 'Grupo ' + p.grupo[-1].upper()
            if p.equipo1.nombre not in grupos22.get(grupo, set()) or p.equipo2.nombre not in grupos22.get(grupo, set()):
                raise CommandError(f'2022: {p.equipo1} vs {p.equipo2} no coincide con {grupo}.')

        creados = actualizados = iguales = conflictos = 0
        with transaction.atomic():
            entradas = [
                (qatar, 'Grupo ' + p.grupo[-1].upper(), p.equipo1, p.goles1, p.equipo2, p.goles2, p.fecha, p.estadio)
                for p in historicos
            ]
            entradas += [
                (mundial26, f'Grupo {letra}', selecciones[a], ga, selecciones[b], gb, None, '')
                for letra, partidos in RESULTADOS_2026.items()
                for (a, ga, b, gb) in partidos
            ]
            for mundial, grupo, equipo1, goles1, equipo2, goles2, fecha, estadio in entradas:
                # Identifica el cruce indistintamente de la orientación de los equipos.
                existentes = list(PartidoGrupo.objects.filter(mundial=mundial, grupo=grupo).filter(
                    Q(equipo1=equipo1, equipo2=equipo2) | Q(equipo1=equipo2, equipo2=equipo1)
                ))
                if len(existentes) > 1:
                    raise CommandError(f'Hay cruces duplicados en BD: {mundial.anio} {equipo1} - {equipo2}. Revisar antes de continuar.')
                if not existentes:
                    creados += 1
                    if not simular:
                        PartidoGrupo.objects.create(mundial=mundial, grupo=grupo, equipo1=equipo1, goles1=goles1,
                            equipo2=equipo2, goles2=goles2, fecha=fecha, estadio=estadio, jugado=True)
                    continue
                partido = existentes[0]
                orientacion_directa = partido.equipo1_id == equipo1.pk
                g_local, g_visitante = (goles1, goles2) if orientacion_directa else (goles2, goles1)
                if partido.jugado and (partido.goles1 != g_local or partido.goles2 != g_visitante):
                    conflictos += 1
                    self.stdout.write(self.style.WARNING(f'CONFLICTO: {mundial.anio} {equipo1} - {equipo2}: marcador previo {partido.goles1}-{partido.goles2}. No se sobrescribe.'))
                    continue
                cambios = []
                if partido.goles1 != g_local:
                    partido.goles1 = g_local; cambios.append('goles1')
                if partido.goles2 != g_visitante:
                    partido.goles2 = g_visitante; cambios.append('goles2')
                if not partido.jugado:
                    partido.jugado = True; cambios.append('jugado')
                if not partido.fecha and fecha:
                    partido.fecha = fecha; cambios.append('fecha')
                if not partido.estadio and estadio:
                    partido.estadio = estadio; cambios.append('estadio')
                if cambios:
                    actualizados += 1
                    if not simular:
                        partido.save(update_fields=cambios)
                else:
                    iguales += 1
            if simular:
                transaction.set_rollback(True)
        self.stdout.write(self.style.SUCCESS(
            f'{"SIMULACIÓN" if simular else "CARGA COMPLETADA"}: '
            f'{creados} nuevos, {actualizados} completados, {iguales} sin cambios, {conflictos} conflictos no sobrescritos.'
        ))
        self.stdout.write('2022: 48 encuentros históricos; 2026: 72 encuentros con resultados. No se modificaron eventos ni posiciones.')
