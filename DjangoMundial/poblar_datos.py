import os
import django

# 1. Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from mundial.models import Mundial, PosicionGrupo, PartidoEliminatoria

def cargar_mundial_2026_real():
    print("⚽ Cargando datos oficiales de la FIFA para el Mundial 2026...")

    # 1. Crear o actualizar la ficha general del Mundial 2026
    mundial_2026, creado = Mundial.objects.get_or_create(
        anio=2026,
        defaults={
            'nombre': 'Copa Mundial de la FIFA 2026',
            'sede': 'Estados Unidos, México, Canadá',
            'descripcion': 'Primera edición de la Copa Mundial disputada con 48 selecciones clasificadas en tres países anfitriones.',
            'campeon': 'España',
            'subcampeon': 'Argentina',
            'tercer_puesto': 'Inglaterra',
            'maximo_goleador': 'Kylian Mbappé',
            'goles_maximo_goleador': 10,
            'mvp_mundial': 'Lamine Yamal',
            'mejor_arquero': 'Unai Simón',
        }
    )

    if not creado:
        mundial_2026.nombre = 'Copa Mundial de la FIFA 2026'
        mundial_2026.sede = 'Estados Unidos, México, Canadá'
        mundial_2026.campeon = 'España'
        mundial_2026.subcampeon = 'Argentina'
        mundial_2026.tercer_puesto = 'Inglaterra'
        mundial_2026.maximo_goleador = 'Kylian Mbappé'
        mundial_2026.goles_maximo_goleador = 10
        mundial_2026.mvp_mundial = 'Lamine Yamal'
        mundial_2026.mejor_arquero = 'Unai Simón'
        mundial_2026.save()
        print("ℹ️ Ficha del Mundial 2026 actualizada con los datos oficiales.")
    else:
        print("✅ Ficha del Mundial 2026 creada.")

    # 2. Posiciones reales de la Fase de Grupos (D al L)
    grupos_oficiales = [
        # GRUPO D
        {'grupo': 'Grupo D', 'equipo': 'Estados Unidos', 'pts': 6, 'pj': 3, 'g': 2, 'e': 0, 'p': 1, 'gf': 8, 'gc': 4, 'forma': 'V,V,D'},
        {'grupo': 'Grupo D', 'equipo': 'Paraguay', 'pts': 4, 'pj': 3, 'g': 1, 'e': 1, 'p': 1, 'gf': 2, 'gc': 4, 'forma': 'D,V,E'},
        {'grupo': 'Grupo D', 'equipo': 'Australia', 'pts': 4, 'pj': 3, 'g': 1, 'e': 1, 'p': 1, 'gf': 2, 'gc': 2, 'forma': 'V,D,E'},
        {'grupo': 'Grupo D', 'equipo': 'Turquía', 'pts': 3, 'pj': 3, 'g': 1, 'e': 0, 'p': 2, 'gf': 3, 'gc': 5, 'forma': 'D,D,V'},

        # GRUPO E
        {'grupo': 'Grupo E', 'equipo': 'Alemania', 'pts': 6, 'pj': 3, 'g': 2, 'e': 0, 'p': 1, 'gf': 10, 'gc': 4, 'forma': 'V,V,D'},
        {'grupo': 'Grupo E', 'equipo': 'Costa de Marfil', 'pts': 6, 'pj': 3, 'g': 2, 'e': 0, 'p': 1, 'gf': 4, 'gc': 2, 'forma': 'V,D,V'},
        {'grupo': 'Grupo E', 'equipo': 'Ecuador', 'pts': 4, 'pj': 3, 'g': 1, 'e': 1, 'p': 1, 'gf': 2, 'gc': 2, 'forma': 'D,E,V'},
        {'grupo': 'Grupo E', 'equipo': 'Curazao', 'pts': 1, 'pj': 3, 'g': 0, 'e': 1, 'p': 2, 'gf': 1, 'gc': 9, 'forma': 'D,E,D'},

        # GRUPO F
        {'grupo': 'Grupo F', 'equipo': 'Países Bajos', 'pts': 7, 'pj': 3, 'g': 2, 'e': 1, 'p': 0, 'gf': 10, 'gc': 4, 'forma': 'E,V,V'},
        {'grupo': 'Grupo F', 'equipo': 'Japón', 'pts': 5, 'pj': 3, 'g': 1, 'e': 2, 'p': 0, 'gf': 7, 'gc': 3, 'forma': 'E,V,E'},
        {'grupo': 'Grupo F', 'equipo': 'Suecia', 'pts': 4, 'pj': 3, 'g': 1, 'e': 1, 'p': 1, 'gf': 7, 'gc': 7, 'forma': 'V,D,E'},
        {'grupo': 'Grupo F', 'equipo': 'Túnez', 'pts': 0, 'pj': 3, 'g': 0, 'e': 0, 'p': 3, 'gf': 2, 'gc': 12, 'forma': 'D,D,D'},

        # GRUPO G
        {'grupo': 'Grupo G', 'equipo': 'Bélgica', 'pts': 5, 'pj': 3, 'g': 1, 'e': 2, 'p': 0, 'gf': 6, 'gc': 2, 'forma': 'E,E,V'},
        {'grupo': 'Grupo G', 'equipo': 'Egipto', 'pts': 5, 'pj': 3, 'g': 1, 'e': 2, 'p': 0, 'gf': 5, 'gc': 3, 'forma': 'E,V,E'},
        {'grupo': 'Grupo G', 'equipo': 'RI de Irán', 'pts': 3, 'pj': 3, 'g': 0, 'e': 3, 'p': 0, 'gf': 3, 'gc': 3, 'forma': 'E,E,E'},
        {'grupo': 'Grupo G', 'equipo': 'Nueva Zelanda', 'pts': 1, 'pj': 3, 'g': 0, 'e': 1, 'p': 2, 'gf': 4, 'gc': 10, 'forma': 'E,D,D'},

        # GRUPO H
        {'grupo': 'Grupo H', 'equipo': 'España', 'pts': 7, 'pj': 3, 'g': 2, 'e': 1, 'p': 0, 'gf': 5, 'gc': 0, 'forma': 'E,V,V'},
        {'grupo': 'Grupo H', 'equipo': 'Cabo Verde', 'pts': 3, 'pj': 3, 'g': 0, 'e': 3, 'p': 0, 'gf': 2, 'gc': 2, 'forma': 'E,E,E'},
        {'grupo': 'Grupo H', 'equipo': 'Uruguay', 'pts': 2, 'pj': 3, 'g': 0, 'e': 2, 'p': 1, 'gf': 3, 'gc': 4, 'forma': 'E,E,D'},
        {'grupo': 'Grupo H', 'equipo': 'Arabia Saudí', 'pts': 2, 'pj': 3, 'g': 0, 'e': 2, 'p': 1, 'gf': 1, 'gc': 5, 'forma': 'E,D,E'},

        # GRUPO I
        {'grupo': 'Grupo I', 'equipo': 'Francia', 'pts': 9, 'pj': 3, 'g': 3, 'e': 0, 'p': 0, 'gf': 10, 'gc': 2, 'forma': 'V,V,V'},
        {'grupo': 'Grupo I', 'equipo': 'Noruega', 'pts': 6, 'pj': 3, 'g': 2, 'e': 0, 'p': 1, 'gf': 8, 'gc': 7, 'forma': 'V,V,D'},
        {'grupo': 'Grupo I', 'equipo': 'Senegal', 'pts': 3, 'pj': 3, 'g': 1, 'e': 0, 'p': 2, 'gf': 8, 'gc': 6, 'forma': 'D,D,V'},
        {'grupo': 'Grupo I', 'equipo': 'Irak', 'pts': 0, 'pj': 3, 'g': 0, 'e': 0, 'p': 3, 'gf': 1, 'gc': 12, 'forma': 'D,D,D'},

        # GRUPO J
        {'grupo': 'Grupo J', 'equipo': 'Argentina', 'pts': 9, 'pj': 3, 'g': 3, 'e': 0, 'p': 0, 'gf': 8, 'gc': 1, 'forma': 'V,V,V'},
        {'grupo': 'Grupo J', 'equipo': 'Austria', 'pts': 4, 'pj': 3, 'g': 1, 'e': 1, 'p': 1, 'gf': 6, 'gc': 6, 'forma': 'V,D,E'},
        {'grupo': 'Grupo J', 'equipo': 'Argelia', 'pts': 4, 'pj': 3, 'g': 1, 'e': 1, 'p': 1, 'gf': 5, 'gc': 7, 'forma': 'D,V,E'},
        {'grupo': 'Grupo J', 'equipo': 'Jordania', 'pts': 0, 'pj': 3, 'g': 0, 'e': 0, 'p': 3, 'gf': 3, 'gc': 8, 'forma': 'D,D,D'},

        # GRUPO K
        {'grupo': 'Grupo K', 'equipo': 'Colombia', 'pts': 7, 'pj': 3, 'g': 2, 'e': 1, 'p': 0, 'gf': 4, 'gc': 1, 'forma': 'V,V,E'},
        {'grupo': 'Grupo K', 'equipo': 'Portugal', 'pts': 5, 'pj': 3, 'g': 1, 'e': 2, 'p': 0, 'gf': 6, 'gc': 1, 'forma': 'E,V,E'},
        {'grupo': 'Grupo K', 'equipo': 'RD Congo', 'pts': 4, 'pj': 3, 'g': 1, 'e': 1, 'p': 1, 'gf': 4, 'gc': 3, 'forma': 'E,D,V'},
        {'grupo': 'Grupo K', 'equipo': 'Uzbekistán', 'pts': 0, 'pj': 3, 'g': 0, 'e': 0, 'p': 3, 'gf': 2, 'gc': 11, 'forma': 'D,D,D'},

        # GRUPO L
        {'grupo': 'Grupo L', 'equipo': 'Inglaterra', 'pts': 7, 'pj': 3, 'g': 2, 'e': 1, 'p': 0, 'gf': 6, 'gc': 2, 'forma': 'V,E,V'},
        {'grupo': 'Grupo L', 'equipo': 'Croacia', 'pts': 6, 'pj': 3, 'g': 2, 'e': 0, 'p': 1, 'gf': 5, 'gc': 5, 'forma': 'D,V,V'},
        {'grupo': 'Grupo L', 'equipo': 'Ghana', 'pts': 4, 'pj': 3, 'g': 1, 'e': 1, 'p': 1, 'gf': 2, 'gc': 2, 'forma': 'V,E,D'},
        {'grupo': 'Grupo L', 'equipo': 'Panamá', 'pts': 0, 'pj': 3, 'g': 0, 'e': 0, 'p': 3, 'gf': 0, 'gc': 4, 'forma': 'D,D,D'},
    ]

    print("\n--- Cargando posiciones de grupos restantes (D al L) ---")
    for fila in grupos_oficiales:
        pos, creada = PosicionGrupo.objects.get_or_create(
            mundial=mundial_2026,
            equipo=fila['equipo'],
            defaults=fila
        )
        if creada:
            print(f"   -> Creado: {fila['grupo']} - {fila['equipo']}")
        else:
            print(f"   -> Ya existía: {fila['grupo']} - {fila['equipo']}")

    # 3. Partidos oficiales de las Eliminatorias
    partidos_eliminatoria_oficiales = [
        # 16vos de final
        {'fase': '16vos', 'equipo1': 'Sudáfrica', 'goles1': 0, 'equipo2': 'Canadá', 'goles2': 1, 'info_extra': '28/06/2026'},
        {'fase': '16vos', 'equipo1': 'Alemania', 'goles1': 1, 'equipo2': 'Paraguay', 'goles2': 1, 'info_extra': 'Penales 3-4'},
        {'fase': '16vos', 'equipo1': 'Países Bajos', 'goles1': 1, 'equipo2': 'Marruecos', 'goles2': 1, 'info_extra': 'Penales 2-3'},
        {'fase': '16vos', 'equipo1': 'Brasil', 'goles1': 2, 'equipo2': 'Japón', 'goles2': 1, 'info_extra': '29/06/2026'},
        {'fase': '16vos', 'equipo1': 'Francia', 'goles1': 3, 'equipo2': 'Suecia', 'goles2': 0, 'info_extra': '30/06/2026'},
        {'fase': '16vos', 'equipo1': 'Costa de Marfil', 'goles1': 1, 'equipo2': 'Noruega', 'goles2': 2, 'info_extra': '30/06/2026'},
        {'fase': '16vos', 'equipo1': 'México', 'goles1': 2, 'equipo2': 'Ecuador', 'goles2': 0, 'info_extra': '30/06/2026'},
        {'fase': '16vos', 'equipo1': 'Inglaterra', 'goles1': 2, 'equipo2': 'RD Congo', 'goles2': 1, 'info_extra': '01/07/2026'},
        {'fase': '16vos', 'equipo1': 'Estados Unidos', 'goles1': 2, 'equipo2': 'Bosnia y Herzegovina', 'goles2': 0, 'info_extra': '01/07/2026'},
        {'fase': '16vos', 'equipo1': 'Bélgica', 'goles1': 3, 'equipo2': 'Senegal', 'goles2': 2, 'info_extra': 'Tiempo Extra'},
        {'fase': '16vos', 'equipo1': 'Portugal', 'goles1': 2, 'equipo2': 'Croacia', 'goles2': 1, 'info_extra': '02/07/2026'},
        {'fase': '16vos', 'equipo1': 'España', 'goles1': 3, 'equipo2': 'Austria', 'goles2': 0, 'info_extra': '02/07/2026'},
        {'fase': '16vos', 'equipo1': 'Suiza', 'goles1': 2, 'equipo2': 'Argelia', 'goles2': 0, 'info_extra': '02/07/2026'},
        {'fase': '16vos', 'equipo1': 'Argentina', 'goles1': 3, 'equipo2': 'Cabo Verde', 'goles2': 2, 'info_extra': 'Tiempo Extra'},
        {'fase': '16vos', 'equipo1': 'Colombia', 'goles1': 1, 'equipo2': 'Ghana', 'goles2': 0, 'info_extra': '03/07/2026'},
        {'fase': '16vos', 'equipo1': 'Australia', 'goles1': 1, 'equipo2': 'Egipto', 'goles2': 1, 'info_extra': 'Penales 2-4'},

        # Octavos de final
        {'fase': 'Octavos', 'equipo1': 'Paraguay', 'goles1': 0, 'equipo2': 'Francia', 'goles2': 1, 'info_extra': '04/07/2026'},
        {'fase': 'Octavos', 'equipo1': 'Canadá', 'goles1': 0, 'equipo2': 'Marruecos', 'goles2': 3, 'info_extra': '04/07/2026'},
        {'fase': 'Octavos', 'equipo1': 'Brasil', 'goles1': 1, 'equipo2': 'Noruega', 'goles2': 2, 'info_extra': '05/07/2026'},
        {'fase': 'Octavos', 'equipo1': 'México', 'goles1': 2, 'equipo2': 'Inglaterra', 'goles2': 3, 'info_extra': '05/07/2026'},
        {'fase': 'Octavos', 'equipo1': 'Portugal', 'goles1': 0, 'equipo2': 'España', 'goles2': 1, 'info_extra': '06/07/2026'},
        {'fase': 'Octavos', 'equipo1': 'Estados Unidos', 'goles1': 1, 'equipo2': 'Bélgica', 'goles2': 4, 'info_extra': '06/07/2026'},
        {'fase': 'Octavos', 'equipo1': 'Argentina', 'goles1': 3, 'equipo2': 'Egipto', 'goles2': 2, 'info_extra': '07/07/2026'},
        {'fase': 'Octavos', 'equipo1': 'Suiza', 'goles1': 0, 'equipo2': 'Colombia', 'goles2': 0, 'info_extra': 'Penales 4-3'},

        # Cuartos de final
        {'fase': 'Cuartos', 'equipo1': 'Francia', 'goles1': 2, 'equipo2': 'Marruecos', 'goles2': 0, 'info_extra': '09/07/2026'},
        {'fase': 'Cuartos', 'equipo1': 'España', 'goles1': 2, 'equipo2': 'Bélgica', 'goles2': 1, 'info_extra': '10/07/2026'},
        {'fase': 'Cuartos', 'equipo1': 'Noruega', 'goles1': 1, 'equipo2': 'Inglaterra', 'goles2': 2, 'info_extra': '11/07/2026'},
        {'fase': 'Cuartos', 'equipo1': 'Argentina', 'goles1': 3, 'equipo2': 'Suiza', 'goles2': 1, 'info_extra': '11/07/2026'},

        # Semifinales
        {'fase': 'Semifinal', 'equipo1': 'Francia', 'goles1': 0, 'equipo2': 'España', 'goles2': 2, 'info_extra': '14/07/2026'},
        {'fase': 'Semifinal', 'equipo1': 'Inglaterra', 'goles1': 1, 'equipo2': 'Argentina', 'goles2': 2, 'info_extra': '15/07/2026'},

        # Tercer Puesto y Final
        {'fase': 'Final', 'equipo1': 'Francia', 'goles1': 4, 'equipo2': 'Inglaterra', 'goles2': 6, 'info_extra': '18/07/2026 - Tercer Puesto'},
        {'fase': 'Final', 'equipo1': 'España', 'goles1': 1, 'equipo2': 'Argentina', 'goles2': 0, 'info_extra': '19/07/2026 - Gran Final (t.e.)'},
    ]

    print("\n--- Cargando cuadro oficial de eliminatorias ---")
    for partido in partidos_eliminatoria_oficiales:
        p, creado = PartidoEliminatoria.objects.get_or_create(
            mundial=mundial_2026,
            fase=partido['fase'],
            equipo1=partido['equipo1'],
            equipo2=partido['equipo2'],
            defaults=partido
        )
        if creado:
            print(f"   -> Partido cargado: {partido['fase']} | {partido['equipo1']} vs {partido['equipo2']}")
        else:
            print(f"   -> Partido ya existía: {partido['fase']} | {partido['equipo1']} vs {partido['equipo2']}")

    print("\n🎉 ¡Carga con los datos oficiales de la FIFA completada con éxito!")

if __name__ == '__main__':
    cargar_mundial_2026_real()