from collections import defaultdict

import unicodedata

from django.views.generic import ListView

from django.shortcuts import render, get_object_or_404, redirect

from django.contrib.auth.forms import UserCreationForm

from django.contrib import messages

from django.contrib.admin.views.decorators import staff_member_required

from django.db.models import Q

from .models import (

    Confederacion,

    Mundial,

    Seleccion,

    Jugador,

    PersonalTecnico,

    PartidoEliminatoria,

    EventoPartido,

    PosicionGrupo,

    PartidoMundial2022,
    HistorialJugador,

)

# ==========================================

# FUNCIONES AUXILIARES

# ==========================================

def normalizar_nombre(nombre):

    """

    Permite comparar nombres con o sin tildes.

    """

    nombre = str(nombre or "").strip().lower()

    nombre = unicodedata.normalize("NFD", nombre)

    return "".join(

        caracter

        for caracter in nombre

        if unicodedata.category(caracter) != "Mn"

    )

def clave_clasificacion(posicion):

    """

    Ordena por:

    1. Mayor cantidad de puntos

    2. Mejor diferencia de gol

    3. Mayor cantidad de goles a favor

    """

    return (

        posicion.pts,

        posicion.gf - posicion.gc,

        posicion.gf,

    )

def clave_mejores_terceros(posicion, anio):

    """

    Ordena a los terceros.

    En el Mundial 2026, Ghana y Ecuador

    terminaron empatados en puntos,

    diferencia de gol y goles a favor.

    Ghana quedó por delante por tener

    mejor puntaje de conducta deportiva.

    """

    conducta = 0

    if anio == 2026:

        nombre = normalizar_nombre(posicion.equipo)

        conducta_2026 = {

            "ghana": -3,

            "ecuador": -5,

        }

        conducta = conducta_2026.get(nombre, 0)

    return (

        posicion.pts,

        posicion.gf - posicion.gc,

        posicion.gf,

        conducta,

    )

def preparar_tablas_mundial(mundial):

    """

    Prepara las tablas de grupos y, cuando

    corresponde, la clasificación de terceros.

    No modifica ni guarda registros.

    """

    posiciones = list(

        PosicionGrupo.objects.filter(

            mundial=mundial

        ).order_by("grupo", "id")

    )

    grupos = defaultdict(list)

    for posicion in posiciones:

        grupos[posicion.grupo].append(posicion)

    # Ordenar los equipos de cada grupo

    grupos_ordenados = {}

    for nombre_grupo, equipos in grupos.items():

        equipos.sort(

            key=clave_clasificacion,

            reverse=True

        )

        grupos_ordenados[nombre_grupo] = equipos

    # Mostrar terceros solamente en formato 2026

    # y cuando estén cargados sus 12 grupos.

    mostrar_terceros = (

        mundial.anio == 2026

        and len(grupos_ordenados) == 12

        and all(

            len(equipos) == 4

            for equipos in grupos_ordenados.values()

        )

    )

    mejores_terceros = []

    ids_terceros_clasificados = set()

    if mostrar_terceros:

        # Extraer el tercer equipo de cada grupo

        for nombre_grupo, equipos in grupos_ordenados.items():

            tercero = equipos[2]

            mejores_terceros.append(tercero)

        # Ordenar los 12 terceros

        mejores_terceros.sort(

            key=lambda pos: clave_mejores_terceros(

                pos, mundial.anio

            ),

            reverse=True

        )

        # Los 8 primeros clasifican

        ids_terceros_clasificados = {

            posicion.pk

            for posicion in mejores_terceros[:8]

        }

    # Preparar datos para el HTML

    tablas_grupos = []

    for nombre_grupo, equipos in sorted(

        grupos_ordenados.items()

    ):

        filas = []

        for numero, posicion in enumerate(equipos, start=1):

            filas.append({

                "posicion": posicion,

                "numero": numero,

                "clasifica_tercero": (

                    numero == 3

                    and posicion.pk in ids_terceros_clasificados

                ),

            })

        tablas_grupos.append({

            "nombre": nombre_grupo,

            "filas": filas,

        })

    # Preparar la tabla lateral

    tabla_terceros = []

    if mostrar_terceros:

        for numero, posicion in enumerate(

            mejores_terceros,

            start=1

        ):

            tabla_terceros.append({

                "numero": numero,

                "posicion": posicion,

                "clasificado": numero <= 8,

            })

    return {

        "tablas_grupos": tablas_grupos,

        "tabla_terceros": tabla_terceros,

        "mostrar_terceros": mostrar_terceros,

    }

# ==========================================

# VISTAS GENERALES

# ==========================================

def inicio(request):

    ultimos_mundiales = Mundial.objects.all().order_by(

        "-anio"

    )[:3]

    return render(request, "inicio.html", {

        "ultimos_mundiales": ultimos_mundiales

    })

def acerca(request):

    return render(request, "acerca.html")

# ==========================================

# DETALLE DEL PARTIDO

# ==========================================

def ordenar_minuto(evento):

    """

    Ordena minutos como:

    34, 45+2, 46, 90+7, 105, etc.

    """

    minuto = str(evento.minuto).replace("'", "").strip()

    try:

        partes = minuto.split("+")

        principal = int(partes[0])

        agregado = (

            int(partes[1])

            if len(partes) > 1

            else 0

        )

        return (principal, agregado, evento.pk)

    except (ValueError, TypeError, IndexError):

        return (999, 0, evento.pk)

def detalle_partido(request, partido_id):

    partido = get_object_or_404(

        PartidoEliminatoria,

        pk=partido_id

    )

    eventos = list(

        EventoPartido.objects.filter(

            partido=partido

        )

    )

    eventos.sort(

        key=ordenar_minuto,

        reverse=True

    )

    goles = [

        evento

        for evento in eventos

        if evento.tipo in (

            "GOL",

            "PENAL",

            "AUTOGOL"

        )

    ]

    tarjetas = [

        evento

        for evento in eventos

        if evento.tipo in (

            "AMARILLA",

            "ROJA",

            "DOBLE_AMARILLA"

        )

    ]

    cambios = [

        evento

        for evento in eventos

        if evento.tipo == "CAMBIO"

    ]

    # Estadísticas para detalle_partido.html

    estadisticas = {

        "goles": len(goles),

        "amarillas": sum(

            1 for evento in tarjetas

            if evento.tipo == "AMARILLA"

        ),

        "rojas": sum(

            1 for evento in tarjetas

            if evento.tipo in (

                "ROJA",

                "DOBLE_AMARILLA"

            )

        ),

        "cambios": len(cambios),

    }

    return render(request, "detalle_partido.html", {

        "partido": partido,

        "eventos": eventos,

        "goles": goles,

        "tarjetas": tarjetas,

        "cambios": cambios,

        "estadisticas": estadisticas,

    })

# ==========================================

# CREAR MUNDIAL

# ==========================================

@staff_member_required

def crear_mundial(request):

    if request.method == "POST":

        pass

    return render(

        request,

        "mundial/crear_mundial.html"

    )

# ==========================================

# REGISTRO

# ==========================================

def registro_view(request):

    if request.method == "POST":

        form = UserCreationForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(

                request,

                "¡Cuenta creada con éxito! Ya puedes iniciar sesión."

            )

            return redirect("login")

    else:

        form = UserCreationForm()

    return render(request, "registro.html", {

        "form": form

    })

# ==========================================

# MUNDIALES

# ==========================================

class MundialListView(ListView):

    """

    Listado de Mundiales con búsqueda y paginación.

    """

    model = Mundial

    template_name = "mundial/mundiales.html"

    context_object_name = "mundiales"

    paginate_by = 6

    def get_queryset(self):

        mundiales = Mundial.objects.all().order_by("-anio")

        q = self.request.GET.get("q", "").strip()

        if q:

            filtros = (

                Q(nombre__icontains=q)

                | Q(sede__icontains=q)

                | Q(campeon__icontains=q)

            )

            if q.isdigit():

                filtros |= Q(anio=int(q))

            mundiales = mundiales.filter(filtros)

        return mundiales

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context["q"] = self.request.GET.get("q", "").strip()

        return context

def detalle_mundial(request, pk):

    mundial = get_object_or_404(

        Mundial,

        pk=pk

    )

    # Nuevas tablas de grupos y terceros

    datos_tablas = preparar_tablas_mundial(mundial)

    # Partidos ordenados por fase y orden

    partidos = list(

        PartidoEliminatoria.objects.filter(

            mundial=mundial

        ).order_by("orden", "pk")

    )

    fases = [

        ("16vos", "16vos de Final"),

        ("Octavos", "Octavos de Final"),

        ("Cuartos", "Cuartos de Final"),

        ("Semifinal", "Semifinales"),

        ("Final", "Gran Final"),

    ]

    fases_cuadro = []

    for codigo, nombre in fases:

        partidos_fase = [

            partido

            for partido in partidos

            if partido.fase == codigo

        ]

        fases_cuadro.append({

            "nombre": nombre,

            "partidos": partidos_fase,

        })

    partidos_tercer_puesto = [

        partido

        for partido in partidos

        if partido.fase == "Tercer Puesto"

    ]

    return render(

        request,

        "mundial/detalle_mundial.html",

        {

            "mundial": mundial,

            "tablas_grupos": datos_tablas["tablas_grupos"],

            "tabla_terceros": datos_tablas["tabla_terceros"],

            "mostrar_terceros": datos_tablas["mostrar_terceros"],

            "fases_cuadro": fases_cuadro,

            "partidos_tercer_puesto": partidos_tercer_puesto,

        }

    )

# ==========================================

# CONFEDERACIONES

# ==========================================

def lista_confederaciones(request):

    confederaciones = Confederacion.objects.all()

    return render(

        request,

        "confederacion/confederaciones.html",

        {

            "confederaciones": confederaciones

        }

    )

def detalle_confederacion(request, pk):

    confederacion = get_object_or_404(

        Confederacion,

        pk=pk

    )

    selecciones = confederacion.selecciones.all()

    return render(

        request,

        "confederacion/detalle_confederacion.html",

        {

            "confederacion": confederacion,

            "selecciones": selecciones

        }

    )

# ==========================================

# SELECCIONES

# ==========================================


# ==========================================
# SELECCIONES DEL MUNDIAL 2026
# Fuente: FIFA - 48 selecciones participantes
# ==========================================

PARTICIPANTES_2026 = {
    "AFC": [
        "Arabia Saudita",
        "Australia",
        "Corea del Sur",
        "Irak",
        "Irán",
        "Japón",
        "Jordania",
        "Qatar",
        "Uzbekistán",
    ],
    "CAF": [
        "Argelia",
        "Cabo Verde",
        "Camerún" if False else "Costa de Marfil",
        "Egipto",
        "Ghana",
        "Marruecos",
        "RD del Congo",
        "Senegal",
        "Sudáfrica",
        "Túnez",
    ],
    "CONCACAF": [
        "Canadá",
        "Curazao",
        "Estados Unidos",
        "Haití",
        "México",
        "Panamá",
    ],
    "CONMEBOL": [
        "Argentina",
        "Brasil",
        "Colombia",
        "Ecuador",
        "Paraguay",
        "Uruguay",
    ],
    "OFC": [
        "Nueva Zelanda",
    ],
    "UEFA": [
        "Alemania",
        "Austria",
        "Bélgica",
        "Bosnia y Herzegovina",
        "Chequia",
        "Croacia",
        "Escocia",
        "España",
        "Francia",
        "Inglaterra",
        "Noruega",
        "Países Bajos",
        "Portugal",
        "Suecia",
        "Suiza",
        "Turquía",
    ],
}


# Diferencias de nombres entre fuentes
ALIAS_SELECCIONES = {
    "republica de corea": "corea del sur",
    "corea republica": "corea del sur",
    "corea del sur": "corea del sur",
    "republica checa": "chequia",
    "czechia": "chequia",
    "curacao": "curazao",
    "cabo verde": "cabo verde",
    "cape verde": "cabo verde",
    "congo dr": "rd del congo",
    "republica democratica del congo": "rd del congo",
    "rd del congo": "rd del congo",
    "costa de marfil": "costa de marfil",
    "cote d'ivoire": "costa de marfil",
    "paises bajos": "paises bajos",
    "holanda": "paises bajos",
    "estados unidos": "estados unidos",
    "usa": "estados unidos",
    "turkiye": "turquia",
}


def clave_seleccion(nombre):
    nombre = normalizar_nombre(nombre)
    return ALIAS_SELECCIONES.get(nombre, nombre)


# ==========================================
# LISTADO DE SELECCIONES
# ==========================================

def selecciones(request):

    mundiales = Mundial.objects.all().order_by("-anio")

    anios_disponibles = list(
        mundiales.values_list("anio", flat=True)
    )

    if 2022 in anios_disponibles:
        anio_predeterminado = 2022
    elif anios_disponibles:
        anio_predeterminado = anios_disponibles[0]
    else:
        anio_predeterminado = None

    try:
        anio_elegido = int(
            request.GET.get("anio", anio_predeterminado)
        )
    except (ValueError, TypeError):
        anio_elegido = anio_predeterminado

    if anio_elegido not in anios_disponibles:
        anio_elegido = anio_predeterminado

    # ======================================
    # OBTENER PARTICIPANTES SEGÚN EL MUNDIAL
    # ======================================

    ids_participantes = set()
    nombres_participantes = set()

    if anio_elegido == 2022:

        # Qatar 2022: los 64 partidos guardados
        partidos = PartidoMundial2022.objects.filter(
            mundial__anio=2022
        )

        ids_participantes.update(
            partidos.values_list("equipo1_id", flat=True)
        )

        ids_participantes.update(
            partidos.values_list("equipo2_id", flat=True)
        )

    elif anio_elegido == 2026:

        # Mundial 2026: los 48 participantes
        # confirmados oficialmente.
        for equipos in PARTICIPANTES_2026.values():
            for equipo in equipos:
                nombres_participantes.add(
                    clave_seleccion(equipo)
                )

    elif anio_elegido is not None:

        # Otros Mundiales: solamente datos cargados
        posiciones = PosicionGrupo.objects.filter(
            mundial__anio=anio_elegido
        ).values_list("equipo", flat=True)

        for equipo in posiciones:
            nombres_participantes.add(
                clave_seleccion(equipo)
            )

        partidos = PartidoEliminatoria.objects.filter(
            mundial__anio=anio_elegido
        ).values_list("equipo1", "equipo2")

        for equipo1, equipo2 in partidos:
            nombres_participantes.add(
                clave_seleccion(equipo1)
            )
            nombres_participantes.add(
                clave_seleccion(equipo2)
            )

    # ======================================
    # SELECCIONES REGISTRADAS EN SQLITE
    # ======================================

    todas_las_selecciones = list(
        Seleccion.objects.select_related(
            "confederacion"
        ).order_by("nombre")
    )

    selecciones_filtradas = [
        seleccion
        for seleccion in todas_las_selecciones
        if (
            seleccion.pk in ids_participantes
            or clave_seleccion(seleccion.nombre)
            in nombres_participantes
        )
    ]

    # ======================================
    # AGRUPAR POR CONFEDERACIÓN
    # ======================================

    confederaciones = Confederacion.objects.all().order_by(
        "nombre"
    )

    selecciones_por_confederacion = []

    for confederacion in confederaciones:

        equipos_confederacion = [
            seleccion
            for seleccion in selecciones_filtradas
            if seleccion.confederacion_id == confederacion.pk
        ]

        if equipos_confederacion:

            selecciones_por_confederacion.append({
                "nombre": confederacion.get_nombre_display(),
                "id": confederacion.nombre.lower(),
                "selecciones": equipos_confederacion,
            })

    return render(
        request,
        "seleccion/selecciones.html",
        {
            "confederaciones": selecciones_por_confederacion,
            "mundiales": mundiales,
            "anio_elegido": anio_elegido,
            "total_selecciones": len(selecciones_filtradas),
        }
    )

def detalle_seleccion(request, pk):

    seleccion = get_object_or_404(Seleccion, pk=pk)

    # Mundiales disponibles en el selector

    anios_disponibles = [

        2026, 2022, 2018, 2014,

        2010, 2006, 2002, 1998

    ]

    # Leer el año elegido en la URL

    try:

        anio_elegido = int(request.GET.get("anio", "2022"))

    except (ValueError, TypeError):

        anio_elegido = 2022

    if anio_elegido not in anios_disponibles:

        anio_elegido = 2022

    mundial_seleccionado = Mundial.objects.filter(

        anio=anio_elegido

    ).first()

    # Inicialmente no asumimos que una selección

    # tenga el mismo plantel en todos los mundiales.

    jugadores = Jugador.objects.none()

    plantel_tecnico = PersonalTecnico.objects.none()

    ultimos_partidos = []

    if anio_elegido == 2022:

        jugadores = Jugador.objects.filter(

            seleccion=seleccion

        ).order_by(

            "numero_camiseta",

            "apellido_nombres"

        )

        plantel_tecnico = PersonalTecnico.objects.filter(

            seleccion=seleccion

        ).order_by("funcion", "apellido")

        partidos = PartidoMundial2022.objects.filter(

            mundial__anio=2022

        ).filter(

            Q(equipo1=seleccion) | Q(equipo2=seleccion)

        ).select_related(

            "equipo1", "equipo2"

        ).order_by(

            "-fecha", "-fifa_match_id"

        )[:4]

        for partido in partidos:

            es_equipo1 = partido.equipo1_id == seleccion.pk

            if es_equipo1:

                rival = partido.equipo2

                gf = partido.goles1

                gc = partido.goles2

                penales_favor = partido.penales1

                penales_contra = partido.penales2

            else:

                rival = partido.equipo1

                gf = partido.goles2

                gc = partido.goles1

                penales_favor = partido.penales2

                penales_contra = partido.penales1

            hubo_penales = bool(

                penales_favor or penales_contra

            )

            if hubo_penales and penales_favor != penales_contra:

                resultado = "V" if penales_favor > penales_contra else "D"

            elif gf > gc:

                resultado = "V"

            elif gf < gc:

                resultado = "D"

            else:

                resultado = "E"

            ultimos_partidos.append({

                "fecha": partido.fecha,

                "fase": partido.fase,

                "rival": rival,

                "goles_propios": gf,

                "goles_rival": gc,

                "penales_propios": penales_favor,

                "penales_rival": penales_contra,

                "hubo_penales": hubo_penales,

                "resultado": resultado,

            })

    contexto = {

        "seleccion": seleccion,

        "anio_elegido": anio_elegido,

        "anios_disponibles": anios_disponibles,

        "mundial_seleccionado": mundial_seleccionado,

        "jugadores": jugadores,

        "arqueros": jugadores.filter(posicion="ARQ"),

        "defensores": jugadores.filter(posicion="DEF"),

        "mediocampistas": jugadores.filter(posicion="MED"),

        "delanteros": jugadores.filter(posicion="DEL"),

        "directores_tecnicos": plantel_tecnico.filter(funcion="DT"),

        "otros_tecnicos": plantel_tecnico.exclude(funcion="DT"),

        "ultimos_partidos": ultimos_partidos,

        "total_jugadores": jugadores.count(),

        "datos_disponibles": anio_elegido == 2022,

    }

    return render(

        request,

        "seleccion/detalle_seleccion.html",

        contexto

    )

# ==========================================

# JUGADORES

# ==========================================

def jugadores(request):

    lista_jugadores = Jugador.objects.all()

    return render(

        request,

        "jugador/jugadores.html",

        {

            "jugadores": lista_jugadores

        }

    )

def detalle_jugador(request, pk):
    jugador = get_object_or_404(Jugador, pk=pk)

    historiales = list(
        HistorialJugador.objects.filter(jugador=jugador)
        .select_related("mundial")
        .order_by("-mundial__anio")
    )

    anios = [h.mundial.anio for h in historiales]
    anio_parametro = request.GET.get("anio", "")

    try:
        anio_elegido = int(anio_parametro) if anio_parametro else (anios[0] if anios else None)
    except (TypeError, ValueError):
        anio_elegido = anios[0] if anios else None

    if anio_elegido not in anios:
        anio_elegido = anios[0] if anios else None

    historial_seleccionado = next(
        (h for h in historiales if h.mundial.anio == anio_elegido),
        None,
    )

    return render(request, "jugador/detalle_jugador.html", {
        "jugador": jugador,
        "historiales": historiales,
        "anio_elegido": anio_elegido,
        "historial_seleccionado": historial_seleccionado,
    })
