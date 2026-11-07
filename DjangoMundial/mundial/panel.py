
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import (
    Collector,
    ProtectedError,
    RestrictedError,
)
from django.forms import (
    CheckboxInput,
    Select,
    modelform_factory,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import (
    Mundial,
    Confederacion,
    Seleccion,
    Jugador,
    HistorialJugador,
    PersonalTecnico,
    PosicionGrupo,
    PartidoEliminatoria,
    EventoPartido,
    PartidoMundial2022,
)


# ==========================================
# SECCIONES DISPONIBLES
# ==========================================

SECCIONES = {
    "mundiales": {
        "modelo": Mundial,
        "titulo": "Mundiales",
        "icono": "fa-trophy",
        "descripcion": "Sedes, campeones, premios e imágenes",
        "columnas": ["anio", "nombre", "sede", "campeon"],
        "busqueda": ["nombre", "sede", "campeon"],
    },
    "confederaciones": {
        "modelo": Confederacion,
        "titulo": "Confederaciones",
        "icono": "fa-globe",
        "descripcion": "Organización de las confederaciones",
        "columnas": ["nombre"],
        "busqueda": ["nombre"],
    },
    "selecciones": {
        "modelo": Seleccion,
        "titulo": "Selecciones",
        "icono": "fa-flag",
        "descripcion": "Países y confederaciones",
        "columnas": ["nombre", "confederacion"],
        "busqueda": ["nombre"],
    },
    "jugadores": {
        "modelo": Jugador,
        "titulo": "Jugadores",
        "icono": "fa-users",
        "descripcion": "Fichas y planteles de futbolistas",
        "columnas": [
            "apellido_nombres",
            "seleccion",
            "posicion",
            "numero_camiseta",
        ],
        "busqueda": [
            "apellido_nombres",
            "pasaporte",
            "seleccion__nombre",
        ],
    },
    "historiales": {
        "modelo": HistorialJugador,
        "titulo": "Estadísticas",
        "icono": "fa-chart-column",
        "descripcion": "Partidos, goles y asistencias por Mundial",
        "columnas": [
            "jugador",
            "mundial",
            "partidos_jugados",
            "goles",
            "asistencias",
        ],
        "busqueda": [
            "jugador__apellido_nombres",
            "jugador__seleccion__nombre",
        ],
    },
    "tecnicos": {
        "modelo": PersonalTecnico,
        "titulo": "Cuerpo técnico",
        "icono": "fa-user-tie",
        "descripcion": "Entrenadores y personal de las selecciones",
        "columnas": ["apellido", "nombre", "funcion", "seleccion"],
        "busqueda": ["nombre", "apellido", "seleccion__nombre"],
    },
    "posiciones": {
        "modelo": PosicionGrupo,
        "titulo": "Posiciones de grupos",
        "icono": "fa-table",
        "descripcion": "Puntos y resultados de la fase de grupos",
        "columnas": ["mundial", "grupo", "equipo", "pts", "pj"],
        "busqueda": ["equipo", "grupo"],
    },
    "eliminatorias": {
        "modelo": PartidoEliminatoria,
        "titulo": "Eliminatorias",
        "icono": "fa-sitemap",
        "descripcion": "Cruces y resultados de los partidos",
        "columnas": [
            "mundial",
            "fase",
            "equipo1",
            "goles1",
            "equipo2",
            "goles2",
        ],
        "busqueda": ["equipo1", "equipo2", "fase"],
    },
    "eventos": {
        "modelo": EventoPartido,
        "titulo": "Eventos de partidos",
        "icono": "fa-futbol",
        "descripcion": "Goles, tarjetas, cambios y faltas",
        "columnas": ["partido", "minuto", "tipo", "jugador"],
        "busqueda": ["jugador", "equipo", "descripcion"],
    },
    "partidos-2022": {
        "modelo": PartidoMundial2022,
        "titulo": "Partidos Qatar 2022",
        "icono": "fa-calendar-days",
        "descripcion": "Resultados y partidos de Qatar 2022",
        "columnas": [
            "fecha",
            "fase",
            "equipo1",
            "goles1",
            "equipo2",
            "goles2",
        ],
        "busqueda": [
            "equipo1__nombre",
            "equipo2__nombre",
            "fase",
        ],
    },
}


# ==========================================
# PERMISOS
# ==========================================

def tiene_permiso(usuario, modelo, accion):
    permiso = (
        f"{modelo._meta.app_label}."
        f"{accion}_{modelo._meta.model_name}"
    )
    return usuario.has_perm(permiso)


def obtener_seccion(seccion):
    from django.http import Http404

    if seccion not in SECCIONES:
        raise Http404("Sección no encontrada")

    return SECCIONES[seccion]


def verificar_permiso(request, modelo, accion):
    from django.core.exceptions import PermissionDenied

    if accion == "view":
        permitido = (
            tiene_permiso(request.user, modelo, "view")
            or tiene_permiso(request.user, modelo, "change")
        )
    else:
        permitido = tiene_permiso(request.user, modelo, accion)

    if not permitido:
        raise PermissionDenied(
            "No tenés permiso para realizar esta operación."
        )


# ==========================================
# PANEL PRINCIPAL
# ==========================================

@staff_member_required(login_url="login")
def inicio_panel(request):

    tarjetas = []

    for clave, configuracion in SECCIONES.items():

        modelo = configuracion["modelo"]

        if not (
            tiene_permiso(request.user, modelo, "view")
            or tiene_permiso(request.user, modelo, "change")
        ):
            continue

        tarjetas.append({
            "clave": clave,
            "titulo": configuracion["titulo"],
            "icono": configuracion["icono"],
            "descripcion": configuracion["descripcion"],
            "cantidad": modelo.objects.count(),
        })

    return render(
        request,
        "panel/panel.html",
        {
            "pagina": "inicio",
            "tarjetas": tarjetas,
        }
    )


# ==========================================
# LISTAR Y BUSCAR
# ==========================================

@staff_member_required(login_url="login")
def listar_registros(request, seccion):

    configuracion = obtener_seccion(seccion)
    modelo = configuracion["modelo"]

    verificar_permiso(request, modelo, "view")

    registros = modelo.objects.all().order_by("-pk")

    relaciones = [
        campo.name
        for campo in modelo._meta.fields
        if campo.is_relation
    ]

    if relaciones:
        registros = registros.select_related(*relaciones)

    busqueda = request.GET.get("q", "").strip()

    if busqueda:
        filtros = Q()

        for campo in configuracion["busqueda"]:
            filtros |= Q(**{f"{campo}__icontains": busqueda})

        registros = registros.filter(filtros).distinct()

    paginador = Paginator(registros, 20)
    pagina = paginador.get_page(request.GET.get("page"))

    filas = []

    for registro in pagina:
        celdas = []

        for nombre_campo in configuracion["columnas"]:

            campo = modelo._meta.get_field(nombre_campo)
            valor = getattr(registro, nombre_campo)

            # Mostrar la descripción de campos con choices
            if campo.choices:
                metodo = getattr(
                    registro,
                    f"get_{nombre_campo}_display",
                    None
                )
                if metodo:
                    valor = metodo()

            celdas.append(
                str(valor) if valor is not None else "—"
            )

        filas.append({
            "pk": registro.pk,
            "celdas": celdas,
        })

    encabezados = [
        str(modelo._meta.get_field(campo).verbose_name).capitalize()
        for campo in configuracion["columnas"]
    ]

    return render(
        request,
        "panel/panel.html",
        {
            "pagina": "listado",
            "seccion": seccion,
            "configuracion": configuracion,
            "filas": filas,
            "encabezados": encabezados,
            "pagina_registros": pagina,
            "busqueda": busqueda,
            "puede_agregar": tiene_permiso(
                request.user, modelo, "add"
            ),
            "puede_editar": tiene_permiso(
                request.user, modelo, "change"
            ),
            "puede_eliminar": tiene_permiso(
                request.user, modelo, "delete"
            ),
        }
    )


# ==========================================
# FORMULARIOS
# ==========================================

def preparar_formulario(modelo, datos=None, archivos=None, instancia=None):

    Formulario = modelform_factory(
        modelo,
        fields="__all__"
    )

    formulario = Formulario(
        data=datos,
        files=archivos,
        instance=instancia,
    )

    for campo in formulario.fields.values():

        if isinstance(campo.widget, CheckboxInput):
            clase = "form-check-input"
        elif isinstance(campo.widget, Select):
            clase = "form-select"
        else:
            clase = "form-control"

        clase_anterior = campo.widget.attrs.get("class", "")

        campo.widget.attrs["class"] = (
            f"{clase_anterior} {clase}"
        ).strip()

    return formulario


@staff_member_required(login_url="login")
def formulario_registro(request, seccion, pk=None):

    configuracion = obtener_seccion(seccion)
    modelo = configuracion["modelo"]

    editando = pk is not None
    accion = "change" if editando else "add"

    verificar_permiso(request, modelo, accion)

    instancia = (
        get_object_or_404(modelo, pk=pk)
        if editando
        else None
    )

    formulario = preparar_formulario(
        modelo,
        datos=request.POST if request.method == "POST" else None,
        archivos=request.FILES if request.method == "POST" else None,
        instancia=instancia,
    )

    if request.method == "POST" and formulario.is_valid():

        formulario.save()

        messages.success(
            request,
            "Los datos se guardaron correctamente."
        )

        return redirect(
            "panel_listado",
            seccion=seccion
        )

    return render(
        request,
        "panel/panel.html",
        {
            "pagina": "formulario",
            "seccion": seccion,
            "configuracion": configuracion,
            "formulario": formulario,
            "editando": editando,
        }
    )


# ==========================================
# ELIMINAR REGISTROS DE FORMA SEGURA
# ==========================================

def puede_eliminar_sin_dependencias(objeto):

    collector = Collector(using=objeto._state.db)

    try:
        collector.collect([objeto])
    except (ProtectedError, RestrictedError):
        return False

    # Impedir eliminaciones en cascada de otros registros
    for modelo, objetos in collector.data.items():
        if modelo != type(objeto) and len(objetos) > 0:
            return False

    for queryset in collector.fast_deletes:
        if queryset.exists():
            return False

    return True


@staff_member_required(login_url="login")
def eliminar_registro(request, seccion, pk):

    configuracion = obtener_seccion(seccion)
    modelo = configuracion["modelo"]

    verificar_permiso(request, modelo, "delete")

    registro = get_object_or_404(modelo, pk=pk)

    if request.method == "POST":

        if not puede_eliminar_sin_dependencias(registro):

            messages.error(
                request,
                "No se puede eliminar este registro porque "
                "tiene información relacionada. "
                "Revisá sus dependencias antes de eliminarlo."
            )

            return redirect(
                "panel_listado",
                seccion=seccion
            )

        registro.delete()

        messages.success(
            request,
            "Registro eliminado correctamente."
        )

        return redirect(
            "panel_listado",
            seccion=seccion
        )

    return render(
        request,
        "panel/panel.html",
        {
            "pagina": "eliminar",
            "seccion": seccion,
            "configuracion": configuracion,
            "registro": registro,
            "puede_borrar": puede_eliminar_sin_dependencias(registro),
        }
    )
