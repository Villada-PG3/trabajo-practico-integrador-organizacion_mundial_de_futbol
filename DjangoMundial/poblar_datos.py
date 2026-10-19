"""
Cargar resultados finales del Mundial 2026 en Django SIN generar JSON.

Fuentes consultadas (octubre de 2026):
- FIFA, resultados de eliminatorias:
  https://www.fifa.com/en/tournaments/mens/worldcup/2026/articles/knockout-stage-match-schedule-bracket
- FIFA, calendario y resultados:
  https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/match-schedule-fixtures-results-teams-stadiums
- FIFA, premios individuales:
  https://www.fifa.com/es/es/articles/rodri-cubarsi-simon-mbappe-premios-copa-mundial-2026
- FIFA Football News, tablas completas de grupos (contrastadas con FIFA):
  https://www.fifaworldcup-news.org/2026/08/fifa-world-cup-2026-final-group.html

Usar desde la carpeta donde esta manage.py:
    python poblar_datos.py    # guarda directamente en la DB

No borra el Mundial ni sus imágenes, no afecta otras ediciones y no crea JSON.
Los partidos del cuadro quedan ordenados por sus cruces reales, no por fecha.
Protege eventos de partidos antiguos frente a borrados accidentales.
"""
import os
import django
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from mundial.models import Mundial, PosicionGrupo, PartidoEliminatoria

# Cada fila: selección, ganados, empatados, perdidos, goles a favor, goles en contra.
# PJ y puntos se calculan, en lugar de introducirlos manualmente.
GRUPOS = {
    'Grupo A': [
        ('México',3,0,0,6,0), ('Sudáfrica',1,1,1,2,3),
        ('Corea del Sur',1,0,2,2,3), ('República Checa',0,1,2,2,6),
    ],
    'Grupo B': [
        ('Suiza',2,1,0,7,3), ('Canadá',1,1,1,8,3),
        ('Bosnia y Herzegovina',1,1,1,5,6), ('Qatar',0,1,2,2,10),
    ],
    'Grupo C': [
        ('Brasil',2,1,0,7,1), ('Marruecos',2,1,0,6,3),
        ('Escocia',1,0,2,1,4), ('Haití',0,0,3,2,8),
    ],
    'Grupo D': [
        ('Estados Unidos',2,0,1,8,4), ('Australia',1,1,1,2,2),
        ('Paraguay',1,1,1,2,4), ('Turquía',1,0,2,3,5),
    ],
    'Grupo E': [
        ('Alemania',2,0,1,10,4), ('Costa de Marfil',2,0,1,4,2),
        ('Ecuador',1,1,1,2,2), ('Curazao',0,1,2,1,9),
    ],
    'Grupo F': [
        ('Países Bajos',2,1,0,10,4), ('Japón',1,2,0,7,3),
        ('Suecia',1,1,1,7,7), ('Túnez',0,0,3,2,12),
    ],
    'Grupo G': [
        ('Bélgica',1,2,0,6,2), ('Egipto',1,2,0,5,3),
        ('Irán',0,3,0,3,3), ('Nueva Zelanda',0,1,2,4,10),
    ],
    'Grupo H': [
        ('España',2,1,0,5,0), ('Cabo Verde',0,3,0,2,2),
        ('Uruguay',0,2,1,3,4), ('Arabia Saudita',0,2,1,1,5),
    ],
    'Grupo I': [
        ('Francia',3,0,0,10,2), ('Noruega',2,0,1,8,7),
        ('Senegal',1,0,2,8,6), ('Irak',0,0,3,1,12),
    ],
    'Grupo J': [
        ('Argentina',3,0,0,8,1), ('Austria',1,1,1,6,6),
        ('Argelia',1,1,1,5,7), ('Jordania',0,0,3,3,8),
    ],
    'Grupo K': [
        ('Colombia',2,1,0,4,1), ('Portugal',1,2,0,6,1),
        ('RD Congo',1,1,1,4,3), ('Uzbekistán',0,0,3,2,11),
    ],
    'Grupo L': [
        ('Inglaterra',2,1,0,6,2), ('Croacia',2,0,1,5,5),
        ('Ghana',1,1,1,2,2), ('Panamá',0,0,3,0,4),
    ],
}

# fase, fecha, equipo1, goles1, equipo2, goles2, nota extra.
# Las tandas se informan aparte: no se suman al marcador.
# AET = resultado luego de prórroga.
PARTIDOS = [
    # Dieciseisavos (ronda de 32)
    ('16vos','28/06/2026','Sudáfrica',0,'Canadá',1,''),
    ('16vos','29/06/2026','Alemania',1,'Paraguay',1,'Penales 3-4'),
    ('16vos','29/06/2026','Países Bajos',1,'Marruecos',1,'Penales 2-3'),
    ('16vos','29/06/2026','Brasil',2,'Japón',1,''),
    ('16vos','30/06/2026','Francia',3,'Suecia',0,''),
    ('16vos','30/06/2026','Costa de Marfil',1,'Noruega',2,''),
    ('16vos','30/06/2026','México',2,'Ecuador',0,''),
    ('16vos','01/07/2026','Inglaterra',2,'RD Congo',1,''),
    ('16vos','01/07/2026','Estados Unidos',2,'Bosnia y Herzegovina',0,''),
    ('16vos','01/07/2026','Bélgica',3,'Senegal',2,'Prórroga'),
    ('16vos','02/07/2026','Portugal',2,'Croacia',1,''),
    ('16vos','02/07/2026','España',3,'Austria',0,''),
    ('16vos','02/07/2026','Suiza',2,'Argelia',0,''),
    ('16vos','03/07/2026','Argentina',3,'Cabo Verde',2,'Prórroga'),
    ('16vos','03/07/2026','Colombia',1,'Ghana',0,''),
    ('16vos','03/07/2026','Australia',1,'Egipto',1,'Penales 2-4'),
    # Octavos
    ('Octavos','04/07/2026','Paraguay',0,'Francia',1,''),
    ('Octavos','04/07/2026','Canadá',0,'Marruecos',3,''),
    ('Octavos','05/07/2026','Brasil',1,'Noruega',2,''),
    ('Octavos','05/07/2026','México',2,'Inglaterra',3,''),
    ('Octavos','06/07/2026','Portugal',0,'España',1,''),
    ('Octavos','06/07/2026','Estados Unidos',1,'Bélgica',4,''),
    ('Octavos','07/07/2026','Argentina',3,'Egipto',2,''),
    ('Octavos','07/07/2026','Suiza',0,'Colombia',0,'Penales 4-3'),
    # Cuartos
    ('Cuartos','09/07/2026','Francia',2,'Marruecos',0,''),
    ('Cuartos','10/07/2026','España',2,'Bélgica',1,''),
    ('Cuartos','11/07/2026','Noruega',1,'Inglaterra',2,'Prórroga'),
    ('Cuartos','11/07/2026','Argentina',3,'Suiza',1,'Prórroga'),
    # Semifinales
    ('Semifinal','14/07/2026','Francia',0,'España',2,''),
    ('Semifinal','15/07/2026','Inglaterra',1,'Argentina',2,''),
    # Tercer puesto
    ('Tercer Puesto','18/07/2026','Francia',4,'Inglaterra',6,''),
    # Final
    ('Final','19/07/2026','España',1,'Argentina',0,'Prórroga'),
]


# Orden real por recorrido de la llave: cada par de partidos alimenta el siguiente.
ORDEN_LLAVE = {
    ('16vos', frozenset(('Sudáfrica', 'Canadá'))): 3,
    ('16vos', frozenset(('Alemania', 'Paraguay'))): 1,
    ('16vos', frozenset(('Países Bajos', 'Marruecos'))): 4,
    ('16vos', frozenset(('Brasil', 'Japón'))): 9,
    ('16vos', frozenset(('Francia', 'Suecia'))): 2,
    ('16vos', frozenset(('Costa de Marfil', 'Noruega'))): 10,
    ('16vos', frozenset(('México', 'Ecuador'))): 11,
    ('16vos', frozenset(('Inglaterra', 'RD Congo'))): 12,
    ('16vos', frozenset(('Estados Unidos', 'Bosnia y Herzegovina'))): 7,
    ('16vos', frozenset(('Bélgica', 'Senegal'))): 8,
    ('16vos', frozenset(('Portugal', 'Croacia'))): 5,
    ('16vos', frozenset(('España', 'Austria'))): 6,
    ('16vos', frozenset(('Suiza', 'Argelia'))): 15,
    ('16vos', frozenset(('Argentina', 'Cabo Verde'))): 13,
    ('16vos', frozenset(('Colombia', 'Ghana'))): 16,
    ('16vos', frozenset(('Australia', 'Egipto'))): 14,
    ('Octavos', frozenset(('Paraguay', 'Francia'))): 1,
    ('Octavos', frozenset(('Canadá', 'Marruecos'))): 2,
    ('Octavos', frozenset(('Brasil', 'Noruega'))): 5,
    ('Octavos', frozenset(('México', 'Inglaterra'))): 6,
    ('Octavos', frozenset(('Portugal', 'España'))): 3,
    ('Octavos', frozenset(('Estados Unidos', 'Bélgica'))): 4,
    ('Octavos', frozenset(('Argentina', 'Egipto'))): 7,
    ('Octavos', frozenset(('Suiza', 'Colombia'))): 8,
    ('Cuartos', frozenset(('Francia', 'Marruecos'))): 1,
    ('Cuartos', frozenset(('España', 'Bélgica'))): 2,
    ('Cuartos', frozenset(('Noruega', 'Inglaterra'))): 3,
    ('Cuartos', frozenset(('Argentina', 'Suiza'))): 4,
    ('Semifinal', frozenset(('Francia', 'España'))): 1,
    ('Semifinal', frozenset(('Inglaterra', 'Argentina'))): 2,
    ('Final', frozenset(('España', 'Argentina'))): 1,
    ("Tercer Puesto", frozenset(("Francia", "Inglaterra"))): 1,
}


def validar_datos():
    assert len(GRUPOS) == 12
    assert sum(len(v) for v in GRUPOS.values()) == 48
    assert len(PARTIDOS) == 32
    for grupo, filas in GRUPOS.items():
        puntos_totales = 0
        goles_favor, goles_contra = 0, 0
        for equipo, g, e, p, gf, gc in filas:
            assert g + e + p == 3, f'PJ incorrectos: {grupo}, {equipo}'
            puntos_totales += 3*g + e
            goles_favor += gf
            goles_contra += gc
        assert goles_favor == goles_contra, f'Goles desbalanceados en {grupo}'
        assert 0 <= puntos_totales <= 18
    claves = set()
    for fase, fecha, e1, g1, e2, g2, extra in PARTIDOS:
        clave = (fase, frozenset((e1, e2)))
        assert clave not in claves, f'Partido repetido: {fase} {e1} vs {e2}'
        claves.add(clave)
        assert e1 != e2


def cargar_mundial_2026():
    validar_datos()

    with transaction.atomic():
        mundial, _ = Mundial.objects.get_or_create(anio=2026)
        mundial.nombre = 'Copa Mundial de la FIFA 2026'
        mundial.sede = 'Estados Unidos, México y Canadá'
        mundial.descripcion = 'Primer Mundial de 48 selecciones, disputado del 11 de junio al 19 de julio de 2026.'
        mundial.campeon = 'España'
        mundial.subcampeon = 'Argentina'
        mundial.tercer_puesto = 'Inglaterra'
        # Premios individuales confirmados por FIFA (19/07/2026).
        mundial.maximo_goleador = 'Kylian Mbappé'
        mundial.goles_maximo_goleador = 10
        mundial.mvp_mundial = 'Rodri'
        mundial.mejor_arquero = 'Unai Simón'
        # Se mantienen intactos imagen_logo e imagen_portada.
        mundial.save()

        # Reutilizar registros existentes de grupos cuando coinciden (mismo Mundial, grupo, equipo).
        ids_posiciones = set()
        for grupo, filas in GRUPOS.items():
            for equipo, g, e, p, gf, gc in filas:
                existentes = list(PosicionGrupo.objects.filter(mundial=mundial, grupo=grupo, equipo=equipo))
                if len(existentes) > 1:
                    raise RuntimeError(f'Posiciones duplicadas: {grupo} / {equipo}')
                obj = existentes[0] if existentes else PosicionGrupo(mundial=mundial, grupo=grupo, equipo=equipo)
                obj.pj = g + e + p
                obj.g, obj.e, obj.p = g, e, p
                obj.gf, obj.gc, obj.pts = gf, gc, 3*g + e
                # No se inventan rachas de forma: 'V,E,D' requiere orden real de partidos.
                obj.forma = ''
                obj.save()
                ids_posiciones.add(obj.pk)

        # Actualizar partidos por equipos y fase, conservando IDs y sus eventos ya editados.
        ids_partidos = set()
        existentes_partidos = list(PartidoEliminatoria.objects.filter(mundial=mundial))
        for fase, fecha, equipo1, goles1, equipo2, goles2, extra in PARTIDOS:
            encontrados = [p for p in existentes_partidos
                           if p.pk not in ids_partidos and p.fase == fase
                           and {p.equipo1, p.equipo2} == {equipo1, equipo2}]
            if len(encontrados) > 1:
                raise RuntimeError(f'Partidos duplicados: {fase} / {equipo1}-{equipo2}')
            obj = encontrados[0] if encontrados else PartidoEliminatoria(mundial=mundial)
            obj.fase = fase
            obj.orden = ORDEN_LLAVE[(fase, frozenset((equipo1, equipo2)))]
            obj.equipo1, obj.equipo2 = equipo1, equipo2
            obj.goles1, obj.goles2 = goles1, goles2
            obj.info_extra = fecha + (f' | {extra}' if extra else '')
            obj.save()
            ids_partidos.add(obj.pk)

        # Borrar los registros falsos/obsoletos SOLO si no hay eventos asociados.
        sobrantes = PartidoEliminatoria.objects.filter(mundial=mundial).exclude(pk__in=ids_partidos)
        con_eventos = [p for p in sobrantes if p.eventos.exists()]
        if con_eventos:
            ejemplos = ', '.join(f'{p.pk}: {p.equipo1}-{p.equipo2}' for p in con_eventos[:5])
            raise RuntimeError('NO se borraron partidos porque algunos tienen eventos cargados. '
                               'Revisalos manualmente antes de eliminar: ' + ejemplos)
        eliminados_partidos = sobrantes.count()
        sobrantes.delete()
        posiciones_sobrantes = PosicionGrupo.objects.filter(mundial=mundial).exclude(pk__in=ids_posiciones)
        eliminadas_posiciones = posiciones_sobrantes.count()
        posiciones_sobrantes.delete()

    print('OK: Mundial 2026 actualizado.')
    print('Grupos:', len(ids_posiciones), '| Eliminatorias:', len(ids_partidos))
    print('Registros antiguos corregidos/descartados:', eliminadas_posiciones, 'posiciones; ', eliminados_partidos, 'partidos.')
    print('No se generaron archivos JSON. Se conservaron las imagenes y otras ediciones.')


if __name__ == '__main__':
    cargar_mundial_2026()
