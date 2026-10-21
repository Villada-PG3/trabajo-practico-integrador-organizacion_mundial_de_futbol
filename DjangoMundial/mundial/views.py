
from collections import defaultdict
import unicodedata

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

from .models import (
    Confederacion,
    Mundial,
    Seleccion,
    Jugador,
    PersonalTecnico,
    PartidoEliminatoria,
    EventoPartido,
    PosicionGrupo,
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

def mundiales(request):

    lista_mundiales = Mundial.objects.all()

    return render(request, "mundial/mundiales.html", {
        "mundiales": lista_mundiales
    })


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

def selecciones(request):

    confederaciones = Confederacion.objects.prefetch_related(
        "selecciones"
    ).all()

    return render(
        request,
        "seleccion/selecciones.html",
        {
            "confederaciones": confederaciones
        }
    )


def detalle_seleccion(request, pk):

    seleccion = get_object_or_404(
        Seleccion,
        pk=pk
    )

    plantel_tecnico = PersonalTecnico.objects.filter(
        seleccion=seleccion
    )

    jugadores = Jugador.objects.filter(
        seleccion=seleccion
    )

    return render(
        request,
        "seleccion/detalle_seleccion.html",
        {
            "seleccion": seleccion,
            "plantel_tecnico": plantel_tecnico,
            "jugadores": jugadores,
        }
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

    jugador = get_object_or_404(
        Jugador,
        pk=pk
    )

    return render(
        request,
        "jugador/detalle_jugador.html",
        {
            "jugador": jugador
        }
    )
