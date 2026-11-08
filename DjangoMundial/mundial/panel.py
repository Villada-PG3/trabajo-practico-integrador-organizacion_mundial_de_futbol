
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import Collector, ProtectedError, RestrictedError
from django.forms import CheckboxInput, Select, modelform_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

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
# SECCIONES DENTRO DE CADA MUNDIAL
# ==========================================

SECCIONES = {
    "posiciones": {
        "modelo": PosicionGrupo,
        "titulo": "Fase de grupos",
        "descripcion": "Grupos, selecciones, puntos y posiciones.",
        "icono": "fa-table",
        "columnas": ["grupo", "equipo", "pj", "pts", "gf", "gc"],
        "busqueda": ["grupo", "equipo"],
    },
    "jugadores": {
        "modelo": HistorialJugador,
        "titulo": "Jugadores y estadísticas",
        "descripcion": "Participaciones, partidos, goles y asistencias.",
        "icono": "fa-users",
        "columnas": [
            "jugador",
            "partidos_jugados",
            "goles",
            "asistencias",
        ],
        "busqueda": [
            "jugador__apellido_nombres",
            "jugador__seleccion__nombre",
        ],
    },
    "eliminatorias": {
        "modelo": PartidoEliminatoria,
        "titulo": "Eliminatorias",
        "descripcion": "Cruces, resultados y fases del Mundial.",
        "icono": "fa-sitemap",
        "columnas": [
            "fase",
            "equipo1",
            "goles1",
            "equipo2",
            "goles2",
        ],
        "busqueda": ["fase", "equipo1", "equipo2"],
    },
    "eventos": {
        "modelo": EventoPartido,
        "titulo": "Eventos",
        "descripcion": "Goles, tarjetas, cambios y faltas.",
        "icono": "fa-futbol",
        "columnas": ["partido", "minuto", "tipo", "jugador"],
        "busqueda": ["jugador", "equipo", "descripcion"],
    },
    "partidos-2022": {
        "modelo": PartidoMundial2022,
        "titulo": "Partidos de Qatar 2022",
        "descripcion": "Partidos y resultados registrados de Qatar.",
        "icono": "fa-calendar-days",
        "columnas": [
            "fase",
            "equipo1",
            "goles1",
            "equipo2",
            "goles2",
        ],
        "busqueda": [
            "fase",
            "equipo1__nombre",
            "equipo2__nombre",
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


def verificar_permiso(request, modelo, accion="view"):
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


def obtener_configuracion(seccion, mundial):
    if seccion not in SECCIONES:
        raise Http404("Sección no encontrada.")

    if seccion == "partidos-2022" and mundial.anio != 2022:
        raise Http404(
            "Esta sección corresponde únicamente al Mundial 2022."
        )

    return SECCIONES[seccion]


def obtener_mundial(request, mundial_id):
    verificar_permiso(request, Mundial)

    return get_object_or_404(
        Mundial,
        pk=mundial_id
    )


# ==========================================
# CONSULTAS FILTRADAS POR MUNDIAL
# ==========================================

def registros_del_mundial(mundial, seccion):

    if seccion == "posiciones":
        return PosicionGrupo.objects.filter(
            mundial=mundial
        )

    if seccion == "jugadores":
        return HistorialJugador.objects.filter(
            mundial=mundial
        ).select_related(
            "jugador",
            "jugador__seleccion",
            "mundial",
        )

    if seccion == "eliminatorias":
        return PartidoEliminatoria.objects.filter(
            mundial=mundial
        )

    if seccion == "eventos":
        return EventoPartido.objects.filter(
            partido__mundial=mundial
        ).select_related("partido")

    if seccion == "partidos-2022" and mundial.anio == 2022:
        return PartidoMundial2022.objects.filter(
            mundial=mundial
        ).select_related("equipo1", "equipo2")

    raise Http404("Sección no disponible para este Mundial.")


def selecciones_participantes(mundial):
    """
    Identifica selecciones usando los registros
    existentes, sin crear relaciones falsas.
    """
    ids = set()

    ids.update(
        HistorialJugador.objects.filter(
            mundial=mundial
        ).exclude(
            jugador__seleccion__isnull=True
        ).values_list(
            "jugador__seleccion_id",
            flat=True
        )
    )

    if mundial.anio == 2022:
        partidos = PartidoMundial2022.objects.filter(
            mundial=mundial
        )

        ids.update(
            partidos.values_list("equipo1_id", flat=True)
        )
        ids.update(
            partidos.values_list("equipo2_id", flat=True)
        )

    nombres = set(
        PosicionGrupo.objects.filter(
            mundial=mundial
        ).values_list("equipo", flat=True)
    )

    partidos_eliminatoria = PartidoEliminatoria.objects.filter(
        mundial=mundial
    )

    nombres.update(
        partidos_eliminatoria.values_list(
            "equipo1",
            flat=True
        )
    )

    nombres.update(
        partidos_eliminatoria.values_list(
            "equipo2",
            flat=True
        )
    )

    return Seleccion.objects.filter(
        Q(pk__in=ids) | Q(nombre__in=nombres)
    ).select_related(
        "confederacion"
    ).distinct().order_by("nombre")


# ==========================================
# CONTEXTO COMPARTIDO
# ==========================================

def contexto_panel(mundial=None):
    mundiales = Mundial.objects.all().order_by("-anio", "pk")

    return {
        "mundiales_panel": mundiales,
        "mundial": mundial,
    }


# ==========================================
# PÁGINA PRINCIPAL
# ==========================================

@staff_member_required(login_url="login")
def inicio_panel(request):
    verificar_permiso(request, Mundial)

    contexto = contexto_panel()

    contexto.update({
        "pagina": "inicio",
        "puede_crear_mundial": tiene_permiso(
            request.user,
            Mundial,
            "add"
        ),
    })

    return render(
        request,
        "panel/panel.html",
        contexto
    )


# ==========================================
# DETALLE DE ADMINISTRACIÓN DE UN MUNDIAL
# ==========================================

@staff_member_required(login_url="login")
def administrar_mundial(request, mundial_id):
    mundial = obtener_mundial(request, mundial_id)

    tarjetas = []

    for clave, configuracion in SECCIONES.items():

        if clave == "partidos-2022" and mundial.anio != 2022:
            continue

        modelo = configuracion["modelo"]

        if not (
            tiene_permiso(request.user, modelo, "view")
            or tiene_permiso(request.user, modelo, "change")
        ):
            continue

        tarjetas.append({
            "clave": clave,
            "titulo": configuracion["titulo"],
            "descripcion": configuracion["descripcion"],
            "icono": configuracion["icono"],
            "cantidad": registros_del_mundial(
                mundial, clave
            ).count(),
        })

    participantes = selecciones_participantes(mundial)

    # Importante: PersonalTecnico aún no tiene
    # relación directa con Mundial.
    # Solo se muestra como referencia por selección.
    tecnicos = PersonalTecnico.objects.filter(
        seleccion__in=participantes
    ).select_related(
        "seleccion"
    ).order_by(
        "seleccion__nombre",
        "apellido"
    )

    contexto = contexto_panel(mundial)

    contexto.update({
        "pagina": "mundial",
        "tarjetas": tarjetas,
        "participantes": participantes,
        "total_participantes": participantes.count(),
        "tecnicos": tecnicos,
        "puede_editar_mundial": tiene_permiso(
            request.user, Mundial, "change"
        ),
    })

    return render(
        request,
        "panel/panel.html",
        contexto
    )


# ==========================================
# LISTADO DE CADA SECCIÓN
# ==========================================

@staff_member_required(login_url="login")
def listado_mundial(request, mundial_id, seccion):
    mundial = obtener_mundial(request, mundial_id)
    config = obtener_configuracion(seccion, mundial)

    modelo = config["modelo"]
    verificar_permiso(request, modelo)

    registros = registros_del_mundial(
        mundial, seccion
    ).order_by("-pk")

    busqueda = request.GET.get("q", "").strip()

    if busqueda:
        filtros = Q()

        for campo in config["busqueda"]:
            filtros |= Q(
                **{f"{campo}__icontains": busqueda}
            )

        registros = registros.filter(
            filtros
        ).distinct()

    pagina = Paginator(
        registros, 25
    ).get_page(
        request.GET.get("page")
    )

    filas = []

    for registro in pagina:
        celdas = []

        for nombre_campo in config["columnas"]:
            campo = modelo._meta.get_field(nombre_campo)
            valor = getattr(registro, nombre_campo)

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
        str(
            modelo._meta.get_field(campo).verbose_name
        ).capitalize()
        for campo in config["columnas"]
    ]

    contexto = contexto_panel(mundial)

    contexto.update({
        "pagina": "listado",
        "seccion": seccion,
        "configuracion": config,
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
    })

    return render(
        request,
        "panel/panel.html",
        contexto
    )


# ==========================================
# FORMULARIOS
# ==========================================

def preparar_formulario(
    modelo,
    datos=None,
    archivos=None,
    instancia=None,
    excluir=()
):
    Formulario = modelform_factory(
        modelo,
        exclude=excluir
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

        anterior = campo.widget.attrs.get("class", "")

        campo.widget.attrs["class"] = (
            f"{anterior} {clase}"
        ).strip()

    return formulario


@staff_member_required(login_url="login")
def formulario_mundial(
    request,
    mundial_id,
    seccion,
    pk=None
):
    mundial = obtener_mundial(request, mundial_id)
    config = obtener_configuracion(seccion, mundial)
    modelo = config["modelo"]

    editando = pk is not None

    verificar_permiso(
        request,
        modelo,
        "change" if editando else "add"
    )

    instancia = None

    if editando:
        # Impide editar registros de otro Mundial
        instancia = get_object_or_404(
            registros_del_mundial(mundial, seccion),
            pk=pk
        )

    excluir = []

    # El Mundial queda fijado por la pestaña
    if seccion != "eventos":
        excluir.append("mundial")
    else:
        # EventoPartido no tiene campo mundial:
        # pertenece al Mundial a través de partido.
        pass

    formulario = preparar_formulario(
        modelo,
        datos=request.POST if request.method == "POST" else None,
        archivos=request.FILES if request.method == "POST" else None,
        instancia=instancia,
        excluir=excluir,
    )

    if seccion == "eventos":
        formulario.fields["partido"].queryset = (
            PartidoEliminatoria.objects.filter(
                mundial=mundial
            ).order_by("fase", "orden")
        )

    if seccion == "jugadores":
        # Mostrar el Mundial exclusivamente
        # mediante la pestaña actual.
        formulario.fields["jugador"].queryset = (
            Jugador.objects.select_related(
                "seleccion"
            ).order_by("apellido_nombres")
        )

    if seccion == "partidos-2022":
        formulario.fields["equipo1"].queryset = (
            Seleccion.objects.order_by("nombre")
        )
        formulario.fields["equipo2"].queryset = (
            Seleccion.objects.order_by("nombre")
        )

    if request.method == "POST" and formulario.is_valid():

        registro = formulario.save(commit=False)

        if seccion != "eventos":
            registro.mundial = mundial

        registro.save()
        formulario.save_m2m()

        messages.success(
            request,
            "Los datos se guardaron correctamente."
        )

        return redirect(
            "panel_mundial_listado",
            mundial_id=mundial.pk,
            seccion=seccion,
        )

    contexto = contexto_panel(mundial)

    contexto.update({
        "pagina": "formulario",
        "seccion": seccion,
        "configuracion": config,
        "formulario": formulario,
        "editando": editando,
    })

    return render(
        request,
        "panel/panel.html",
        contexto
    )


# ==========================================
# CREAR O EDITAR UN MUNDIAL
# ==========================================

@staff_member_required(login_url="login")
def formulario_registro(request, seccion, pk=None):

    # Compatibilidad con las rutas anteriores.
    # Solo Mundiales puede crearse desde el panel general.
    if seccion != "mundiales":
        return redirect("panel_inicio")

    editando = pk is not None

    verificar_permiso(
        request,
        Mundial,
        "change" if editando else "add"
    )

    instancia = (
        get_object_or_404(Mundial, pk=pk)
        if editando else None
    )

    formulario = preparar_formulario(
        Mundial,
        datos=request.POST if request.method == "POST" else None,
        archivos=request.FILES if request.method == "POST" else None,
        instancia=instancia,
    )

    if request.method == "POST" and formulario.is_valid():

        nuevo_anio = formulario.cleaned_data["anio"]

        duplicado = Mundial.objects.filter(
            anio=nuevo_anio
        )

        if instancia is not None:
            duplicado = duplicado.exclude(pk=instancia.pk)

        if duplicado.exists():
            formulario.add_error(
                "anio",
                "Ya existe un Mundial registrado con este año."
            )
        else:
            mundial = formulario.save()

            messages.success(
                request,
                "Mundial guardado correctamente."
            )

            return redirect(
                "panel_mundial",
                mundial_id=mundial.pk
            )

    contexto = contexto_panel()

    contexto.update({
        "pagina": "formulario_mundial",
        "formulario": formulario,
        "editando": editando,
        "mundial_editado": instancia,
    })

    return render(
        request,
        "panel/panel.html",
        contexto
    )


# ==========================================
# ELIMINACIÓN PROTEGIDA
# ==========================================

def puede_eliminar_sin_dependencias(objeto):
    collector = Collector(
        using=objeto._state.db
    )

    try:
        collector.collect([objeto])
    except (ProtectedError, RestrictedError):
        return False

    for modelo, objetos in collector.data.items():
        if modelo != type(objeto) and len(objetos) > 0:
            return False

    for queryset in collector.fast_deletes:
        if queryset.exists():
            return False

    return True


@staff_member_required(login_url="login")
def eliminar_mundial_registro(
    request,
    mundial_id,
    seccion,
    pk
):
    mundial = obtener_mundial(request, mundial_id)
    config = obtener_configuracion(seccion, mundial)
    modelo = config["modelo"]

    verificar_permiso(request, modelo, "delete")

    registro = get_object_or_404(
        registros_del_mundial(mundial, seccion),
        pk=pk
    )

    puede_borrar = puede_eliminar_sin_dependencias(
        registro
    )

    if request.method == "POST":

        if not puede_borrar:
            messages.error(
                request,
                "No se puede eliminar porque hay "
                "información relacionada."
            )
        else:
            registro.delete()

            messages.success(
                request,
                "Registro eliminado correctamente."
            )

        return redirect(
            "panel_mundial_listado",
            mundial_id=mundial.pk,
            seccion=seccion
        )

    contexto = contexto_panel(mundial)

    contexto.update({
        "pagina": "eliminar",
        "registro": registro,
        "seccion": seccion,
        "configuracion": config,
        "puede_borrar": puede_borrar,
    })

    return render(
        request,
        "panel/panel.html",
        contexto
    )


# ==========================================
# RUTAS ANTERIORES DEL PANEL
# ==========================================

@staff_member_required(login_url="login")
def listar_registros(request, seccion):
    if seccion == "mundiales":
        return redirect("panel_inicio")

    return redirect("panel_inicio")


@staff_member_required(login_url="login")
def eliminar_registro(request, seccion, pk):
    # No permitimos eliminar Mundiales desde
    # una ruta general: podrían tener muchos datos.
    return redirect("panel_inicio")
