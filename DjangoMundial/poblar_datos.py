import os
import django

# 1. Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from mundial.models import Mundial, PosicionGrupo, PartidoEliminatoria

def cargar_mundial_2026_limpio():
    print("⚽ Limpiando base de datos y cargando los datos correctos del Mundial 2026...")

    # 1. Obtener o crear la ficha del Mundial 2026
    mundial_2026, _ = Mundial.objects.get_or_create(
        anio=2026,
        defaults={
            'nombre': 'Copa Mundial de la FIFA 2026',
            'sede': 'Estados Unidos, México, Canadá',
            'descripcion': 'Primera edición de la Copa Mundial disputada con 48 selecciones.',
            'campeon': 'España',
            'subcampeon': 'Argentina',
            'tercer_puesto': 'Inglaterra',
            'maximo_goleador': 'Kylian Mbappé',
            'goles_maximo_goleador': 10,
            'mvp_mundial': 'Lamine Yamal',
            'mejor_arquero': 'Unai Simón',
        }
    )

    # 2. LIMPIEZA TOTAL DE REGISTROS DE 2026 (Elimina duplicados y errores)
    mundial_2026.posiciones.all().delete()
    mundial_2026.partidos_eliminatoria.all().delete()
    print("🧹 Posiciones y eliminatorias anteriores limpiadas correctamente.")

    # 3. CARGA DE TODOS LOS GRUPOS (Grupo A al L)
    todos_los_grupos = [
        # GRUPO A
        {'grupo': 'Grupo A', 'equipo': 'México', 'pts': 9, 'pj': 3, 'g': 3, 'e': 0, 'p': 0, 'gf': 6, 'gc': 0, 'forma': 'V,V,V'},
        {'grupo': 'Grupo A', 'equipo': 'Sudáfrica', 'pts': 4, 'pj': 3, 'g': 1, 'e': 1, 'p': 1, 'gf': 2, 'gc': 3, 'forma': 'V,E,D'},
        {'grupo': 'Grupo A', 'equipo': 'Corea del Sur', 'pts': 3, 'pj': 3, 'g': 1, 'e': 0, 'p': 2, 'gf': 2, 'gc': 3, 'forma': 'D,D,V'},
        {'grupo': 'Grupo A', 'equipo': 'República Checa', 'pts': 1, 'pj': 3, 'g': 0, 'e': 1, 'p': 2, 'gf': 2, 'gc': 6, 'forma': 'D,E,D'},

        # GRUPO B
        {'grupo': 'Grupo B', 'equipo': 'Canadá', 'pts': 7, 'pj': 3, 'g': 2, 'e': 1, 'p': 0, 'gf': 5, 'gc': 1, 'forma': 'V,E,V'},
        {'grupo': 'Grupo B', 'equipo': 'Marruecos', 'pts': 6, 'pj': 3, 'g': 2, 'e': 0, 'p': 1, 'gf': 4, 'gc': 2, 'forma': 'V,V,D'},
        {'grupo': 'Grupo B', 'equipo': 'Italia', 'pts': 4, 'pj': 3, 'g': 1, 'e': 1, 'p': 1, 'gf': 3, 'gc': 3, 'forma': 'D,V,E'},
        {'grupo': 'Grupo B', 'equipo': 'Qatar', 'pts': 0, 'pj': 3, 'g': 0, 'e': 0, 'p': 3, 'gf': 0, 'gc': 6, 'forma': 'D,D,D'},

        # GRUPO C
        {'grupo': 'Grupo C', 'equipo': 'Estados Unidos', 'pts': 7, 'pj': 3, 'g': 2, 'e': 1, 'p': 0, 'gf': 6, 'gc': 2, 'forma': 'V,V,E'},
        {'grupo': 'Grupo C', 'equipo': 'Senegal', 'pts': 6, 'pj': 3, 'g': 2, 'e': 0, 'p': 1, 'gf': 5, 'gc': 3, 'forma': 'V,D,V'},
        {'grupo': 'Grupo C', 'equipo': 'Suiza', 'pts': 3, 'pj': 3, 'g': 1, 'e': 0, 'p': 2, 'gf': 3, 'gc': 5, 'forma': 'D,V,D'},
        {'grupo': 'Grupo C', 'equipo': 'Honduras', 'pts': 1, 'pj': 3, 'g': 0, 'e': 1, 'p': 2, 'gf': 1, 'gc': 5, 'forma': 'E,D,D'},

        # GRUPO D
        {'grupo': 'Grupo D', 'equipo': 'Brasil', 'pts': 9, 'pj': 3, 'g': 3, 'e': 0, 'p': 0, 'gf': 7, 'gc': 1, 'forma': 'V,V,V'},
        {'grupo': 'Grupo D', 'equipo': 'Colombia', 'pts': 6, 'pj': 3, 'g': 2, 'e': 0, 'p': 1, 'gf': 5, 'gc': 3, 'forma': 'V,D,V'},
        {'grupo': 'Grupo D', 'equipo': 'Japón', 'pts': 3, 'pj': 3, 'g': 1, 'e': 0, 'p': 2, 'gf': 3, 'gc': 5, 'forma': 'D,V,D'},
        {'grupo': 'Grupo D', 'equipo': 'Nigeria', 'pts': 0, 'pj': 3, 'g': 0, 'e': 0, 'p': 3, 'gf': 1, 'gc': 7, 'forma': 'D,D,D'},

        # GRUPO E
        {'grupo': 'Grupo E', 'equipo': 'Alemania', 'pts': 6, 'pj': 3, 'g': 2, 'e': 0, 'p': 1, 'gf': 10, 'gc': 4, 'forma': 'V,V,D'},
        {'grupo': 'Grupo E', 'equipo': 'Costa de Marfil', 'pts': 6, 'pj': 3, 'g': 2, 'e': 0, 'p': 1, 'gf': 4, 'gc': 2, 'forma': 'V,D,V'},
        {'grupo': 'Grupo E', 'equipo': 'Ecuador', 'pts': 4, 'pj': 3, 'g': 1, 'e': 1, 'p': 1, 'gf': 2, 'gc': 2, 'forma': 'D,E,V'},
        {'grupo': 'Grupo E', 'equipo': 'Curazao', 'pts': 1, 'pj': 3, 'g': 0, 'e': 1, 'p': 2, 'gf': 1, 'gc': 9, 'forma': 'D,E,D'},

        # GRUPO F
        {'grupo': 'Grupo F', 'equipo': 'Países Bajos', 'pts': 7, 'pj': 3, 'g': 2, 'e': 1, 'p': 0, 'gf': 10, 'gc': 4, 'forma': 'E,V,V'},
        {'grupo': 'Grupo F', 'equipo': 'Croacia', 'pts': 5, 'pj': 3, 'g': 1, 'e': 2, 'p': 0, 'gf': 7, 'gc': 3, 'forma': 'E,V,E'},
        {'grupo': 'Grupo F', 'equipo': 'Suecia', 'pts': 4, 'pj': 3, 'g': 1, 'e': 1, 'p': 1, 'gf': 7, 'gc': 7, 'forma': 'V,D,E'},
        {'grupo': 'Grupo F', 'equipo': 'Túnez', 'pts': 0, 'pj': 3, 'g': 0, 'e': 0, 'p': 3, 'gf': 2, 'gc': 12, 'forma': 'D,D,D'},

        # GRUPO G
        {'grupo': 'Grupo G', 'equipo': 'Bélgica', 'pts': 5, 'pj': 3, 'g': 1, 'e': 2, 'p': 0, 'gf': 6, 'gc': 2, 'forma': 'E,E,V'},
        {'grupo': 'Grupo G', 'equipo': 'Egipto', 'pts': 5, 'pj': 3, 'g': 1, 'e': 2, 'p': 0, 'gf': 5, 'gc': 3, 'forma': 'E,V,E'},
        {'grupo': 'Grupo G', 'equipo': 'Irán', 'pts': 3, 'pj': 3, 'g': 0, 'e': 3, 'p': 0, 'gf': 3, 'gc': 3, 'forma': 'E,E,E'},
        {'grupo': 'Grupo G', 'equipo': 'Nueva Zelanda', 'pts': 1, 'pj': 3, 'g': 0, 'e': 1, 'p': 2, 'gf': 4, 'gc': 10, 'forma': 'E,D,D'},

        # GRUPO H
        {'grupo': 'Grupo H', 'equipo': 'España', 'pts': 7, 'pj': 3, 'g': 2, 'e': 1, 'p': 0, 'gf': 5, 'gc': 0, 'forma': 'E,V,V'},
        {'grupo': 'Grupo H', 'equipo': 'Cabo Verde', 'pts': 3, 'pj': 3, 'g': 0, 'e': 3, 'p': 0, 'gf': 2, 'gc': 2, 'forma': 'E,E,E'},
        {'grupo': 'Grupo H', 'equipo': 'Uruguay', 'pts': 2, 'pj': 3, 'g': 0, 'e': 2, 'p': 1, 'gf': 3, 'gc': 4, 'forma': 'E,E,D'},
        {'grupo': 'Grupo H', 'equipo': 'Arabia Saudí', 'pts': 2, 'pj': 3, 'g': 0, 'e': 2, 'p': 1, 'gf': 1, 'gc': 5, 'forma': 'E,D,E'},

        # GRUPO I
        {'grupo': 'Grupo I', 'equipo': 'Francia', 'pts': 9, 'pj': 3, 'g': 3, 'e': 0, 'p': 0, 'gf': 10, 'gc': 2, 'forma': 'V,V,V'},
        {'grupo': 'Grupo I', 'equipo': 'Noruega', 'pts': 6, 'pj': 3, 'g': 2, 'e': 0, 'p': 1, 'gf': 8, 'gc': 7, 'forma': 'V,V,D'},
        {'grupo': 'Grupo I', 'equipo': 'Argelia', 'pts': 3, 'pj': 3, 'g': 1, 'e': 0, 'p': 2, 'gf': 5, 'gc': 7, 'forma': 'D,V,D'},
        {'grupo': 'Grupo I', 'equipo': 'Irak', 'pts': 0, 'pj': 3, 'g': 0, 'e': 0, 'p': 3, 'gf': 1, 'gc': 12, 'forma': 'D,D,D'},

        # GRUPO J
        {'grupo': 'Grupo J', 'equipo': 'Argentina', 'pts': 9, 'pj': 3, 'g': 3, 'e': 0, 'p': 0, 'gf': 8, 'gc': 1, 'forma': 'V,V,V'},
        {'grupo': 'Grupo J', 'equipo': 'Austria', 'pts': 4, 'pj': 3, 'g': 1, 'e': 1, 'p': 1, 'gf': 6, 'gc': 6, 'forma': 'V,D,E'},
        {'grupo': 'Grupo J', 'equipo': 'RD Congo', 'pts': 4, 'pj': 3, 'g': 1, 'e': 1, 'p': 1, 'gf': 4, 'gc': 3, 'forma': 'E,D,V'},
        {'grupo': 'Grupo J', 'equipo': 'Jordania', 'pts': 0, 'pj': 3, 'g': 0, 'e': 0, 'p': 3, 'gf': 3, 'gc': 8, 'forma': 'D,D,D'},

        # GRUPO K
        {'grupo': 'Grupo K', 'equipo': 'Colombia', 'pts': 7, 'pj': 3, 'g': 2, 'e': 1, 'p': 0, 'gf': 4, 'gc': 1, 'forma': 'V,V,E'},
        {'grupo': 'Grupo K', 'equipo': 'Portugal', 'pts': 5, 'pj': 3, 'g': 1, 'e': 2, 'p': 0, 'gf': 6, 'gc': 1, 'forma': 'E,V,E'},
        {'grupo': 'Grupo K', 'equipo': 'Ghana', 'pts': 4, 'pj': 3, 'g': 1, 'e': 1, 'p': 1, 'gf': 2, 'gc': 2, 'forma': 'V,E,D'},
        {'grupo': 'Grupo K', 'equipo': 'Uzbekistán', 'pts': 0, 'pj': 3, 'g': 0, 'e': 0, 'p': 3, 'gf': 2, 'gc': 11, 'forma': 'D,D,D'},

        # GRUPO L
        {'grupo': 'Grupo L', 'equipo': 'Inglaterra', 'pts': 7, 'pj': 3, 'g': 2, 'e': 1, 'p': 0, 'gf': 6, 'gc': 2, 'forma': 'V,E,V'},
        {'grupo': 'Grupo L', 'equipo': 'Irlanda', 'pts': 4, 'pj': 3, 'g': 1, 'e': 1, 'p': 1, 'gf': 3, 'gc': 4, 'forma': 'E,V,D'},
        {'grupo': 'Grupo L', 'equipo': 'Australia', 'pts': 4, 'pj': 3, 'g': 1, 'e': 1, 'p': 1, 'gf': 2, 'gc': 3, 'forma': 'D,E,V'},
        {'grupo': 'Grupo L', 'equipo': 'Panamá', 'pts': 0, 'pj': 3, 'g': 0, 'e': 0, 'p': 3, 'gf': 0, 'gc': 4, 'forma': 'D,D,D'},
    ]

    print("--- Guardando posiciones ordenadas por grupo ---")
    for pos in todos_los_grupos:
        PosicionGrupo.objects.create(mundial=mundial_2026, **pos)

    # 4. CUADRO DE ELIMINATORIAS COMPLETO
    partidos_eliminatoria = [
        # 16VOS DE FINAL
        {'fase': '16vos', 'equipo1': 'Francia', 'goles1': 3, 'equipo2': 'Rusia', 'goles2': 0, 'info_extra': '30/06 18:00'},
        {'fase': '16vos', 'equipo1': 'Sudáfrica', 'goles1': 0, 'equipo2': 'Canadá', 'goles2': 1, 'info_extra': '28/06 16:00'},
        {'fase': '16vos', 'equipo1': 'Holanda', 'goles1': 1, 'equipo2': 'Marruecos', 'goles2': 1, 'info_extra': 'Penales 2-3 | 28/06 22:00'},
        {'fase': '16vos', 'equipo1': 'Portugal', 'goles1': 2, 'equipo2': 'Croacia', 'goles2': 1, 'info_extra': '01/07 20:00'},
        {'fase': '16vos', 'equipo1': 'España', 'goles1': 3, 'equipo2': 'Austria', 'goles2': 0, 'info_extra': '01/07 16:00'},
        {'fase': '16vos', 'equipo1': 'Estados Unidos', 'goles1': 2, 'equipo2': 'Bosnia-Herzegovina', 'goles2': 0, 'info_extra': '01/07 21:00'},
        {'fase': '16vos', 'equipo1': 'Bélgica', 'goles1': 3, 'equipo2': 'Senegal', 'goles2': 2, 'info_extra': '01/07 17:00'},
        {'fase': '16vos', 'equipo1': 'Brasil', 'goles1': 2, 'equipo2': 'Japón', 'goles2': 1, 'info_extra': '28/06 14:00'},
        {'fase': '16vos', 'equipo1': 'Costa de Marfil', 'goles1': 1, 'equipo2': 'Noruega', 'goles2': 2, 'info_extra': '30/06 14:00'},
        {'fase': '16vos', 'equipo1': 'México', 'goles1': 2, 'equipo2': 'Ecuador', 'goles2': 0, 'info_extra': '30/06 22:00'},
        {'fase': '16vos', 'equipo1': 'Inglaterra', 'goles1': 2, 'equipo2': 'RD Congo', 'goles2': 1, 'info_extra': '01/07 13:00'},
        {'fase': '16vos', 'equipo1': 'Argentina', 'goles1': 3, 'equipo2': 'Cabo Verde', 'goles2': 2, 'info_extra': '03/07 19:00'},
        {'fase': '16vos', 'equipo1': 'Australia', 'goles1': 1, 'equipo2': 'Egipto', 'goles2': 1, 'info_extra': 'Penales 2-4 | 03/07 15:00'},
        {'fase': '16vos', 'equipo1': 'Suiza', 'goles1': 2, 'equipo2': 'Argelia', 'goles2': 0, 'info_extra': '03/07 00:00'},
        {'fase': '16vos', 'equipo1': 'Colombia', 'goles1': 1, 'equipo2': 'Ghana', 'goles2': 0, 'info_extra': '03/07 22:30'},

        # OCTAVOS DE FINAL
        {'fase': 'Octavos', 'equipo1': 'Francia', 'goles1': 1, 'equipo2': 'Canadá', 'goles2': 0, 'info_extra': '04/07 17:00'},
        {'fase': 'Octavos', 'equipo1': 'Canadá', 'goles1': 0, 'equipo2': 'Marruecos', 'goles2': 3, 'info_extra': '04/07 14:00'},
        {'fase': 'Octavos', 'equipo1': 'Portugal', 'goles1': 0, 'equipo2': 'España', 'goles2': 1, 'info_extra': '05/07 16:00'},
        {'fase': 'Octavos', 'equipo1': 'Estados Unidos', 'goles1': 1, 'equipo2': 'Bélgica', 'goles2': 4, 'info_extra': '06/07 21:00'},
        {'fase': 'Octavos', 'equipo1': 'Brasil', 'goles1': 1, 'equipo2': 'Noruega', 'goles2': 2, 'info_extra': '05/07 17:00'},
        {'fase': 'Octavos', 'equipo1': 'México', 'goles1': 2, 'equipo2': 'Inglaterra', 'goles2': 3, 'info_extra': '05/07 22:00'},
        {'fase': 'Octavos', 'equipo1': 'Argentina', 'goles1': 3, 'equipo2': 'Egipto', 'goles2': 2, 'info_extra': '07/07 13:00'},
        {'fase': 'Octavos', 'equipo1': 'Suiza', 'goles1': 0, 'equipo2': 'Colombia', 'goles2': 0, 'info_extra': 'Penales 4-5 | 07/07 17:00'},

        # CUARTOS DE FINAL
        {'fase': 'Cuartos', 'equipo1': 'Francia', 'goles1': 2, 'equipo2': 'Marruecos', 'goles2': 0, 'info_extra': '09/07 17:00'},
        {'fase': 'Cuartos', 'equipo1': 'España', 'goles1': 2, 'equipo2': 'Bélgica', 'goles2': 1, 'info_extra': '10/07 16:00'},
        {'fase': 'Cuartos', 'equipo1': 'Noruega', 'goles1': 1, 'equipo2': 'Inglaterra', 'goles2': 2, 'info_extra': '11/07 18:00'},
        {'fase': 'Cuartos', 'equipo1': 'Argentina', 'goles1': 3, 'equipo2': 'Suiza', 'goles2': 1, 'info_extra': '11/07 22:00'},

        # SEMIFINALES
        {'fase': 'Semifinal', 'equipo1': 'Francia', 'goles1': 0, 'equipo2': 'España', 'goles2': 2, 'info_extra': '14/07 16:00'},
        {'fase': 'Semifinal', 'equipo1': 'Inglaterra', 'goles1': 1, 'equipo2': 'Argentina', 'goles2': 2, 'info_extra': '15/07 16:00'},

        # GRAN FINAL
        {'fase': 'Final', 'equipo1': 'España', 'goles1': 1, 'equipo2': 'Argentina', 'goles2': 0, 'info_extra': '19/07 16:00 - Gran Final'},
    ]

    print("--- Guardando partidos de eliminatorias ---")
    for partido in partidos_eliminatoria:
        PartidoEliminatoria.objects.create(mundial=mundial_2026, **partido)

    print("\n🎉 ¡Base de datos del Mundial 2026 limpiada y cargada exitosamente!")

if __name__ == '__main__':
    cargar_mundial_2026_limpio()