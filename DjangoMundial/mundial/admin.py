from django.contrib import admin
from django.utils.html import format_html
from .models import Mundial, PosicionGrupo, PartidoEliminatoria
from .models import (
    Confederacion,
    EventoPartido,
    HistorialJugador,
    Jugador,
    PersonalTecnico,
    Seleccion,
)

@admin.register(Confederacion)
class ConfederacionAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


class JugadorInline(admin.TabularInline):
    model = Jugador
    extra = 1
    fields = ('apellido_nombres', 'pasaporte', 'posicion', 'numero_camiseta', 'equipo_actual', 'pais_equipo')


class PersonalTecnicoInline(admin.TabularInline):
    model = PersonalTecnico
    extra = 1
    fields = ('nombre', 'apellido', 'pasaporte', 'funcion')


@admin.register(Seleccion)
class SeleccionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'confederacion')
    list_filter = ('confederacion',)
    search_fields = ('nombre',)
    inlines = [PersonalTecnicoInline, JugadorInline]


@admin.register(PersonalTecnico)
class PersonalTecnicoAdmin(admin.ModelAdmin):
    list_display = ('apellido', 'nombre', 'funcion', 'seleccion', 'pasaporte')
    list_filter = ('funcion', 'seleccion')
    search_fields = ('nombre', 'apellido', 'pasaporte')


@admin.register(Jugador)
class JugadorAdmin(admin.ModelAdmin):
    list_display = (
        "apellido_nombres", "pasaporte", "edad", "posicion",
        "equipo_actual", "pais_equipo", "numero_camiseta", "seleccion",
    )
    search_fields = ("apellido_nombres", "pasaporte", "equipo_actual")
    list_filter = ("posicion", "seleccion")

@admin.register(HistorialJugador)
class HistorialJugadorAdmin(admin.ModelAdmin):
    list_display = ("jugador", "mundial", "partidos_jugados", "goles")
    list_filter = ("mundial",)
    search_fields = ("jugador__apellido_nombres",)
    ordering = ("-mundial__anio",)

class EventoPartidoInline(admin.TabularInline):
    model = EventoPartido
    extra = 1
    fields = (
        "minuto", "tipo", "equipo", "jugador", "jugador_entra",
        "jugador_sale", "descripcion",
    )

@admin.register(PartidoEliminatoria)
class PartidoEliminatoriaAdmin(admin.ModelAdmin):
    list_display = (
        "mundial", "fase", "orden", "equipo1", "goles1",
        "equipo2", "goles2", "info_extra",
    )
    list_filter = ("mundial", "fase")
    list_editable = ("orden",)
    search_fields = ("equipo1", "equipo2")
    ordering = ("-mundial__anio", "fase", "orden", "pk")
    inlines = [EventoPartidoInline]

class PosicionGrupoInline(admin.TabularInline):
    model = PosicionGrupo
    extra = 4
    fields = ("grupo", "equipo", "pts", "pj", "gf", "gc", "g", "e", "p", "forma")

class PartidoEliminatoriaInline(admin.TabularInline):
    model = PartidoEliminatoria
    extra = 2
    fields = ("fase", "orden", "equipo1", "goles1", "equipo2", "goles2", "info_extra")

@admin.register(Mundial)
class MundialAdmin(admin.ModelAdmin):
    list_display = ("anio", "sede", "campeon", "mvp_mundial", "maximo_goleador", "mostrar_logo")
    list_filter = ("anio", "sede")
    search_fields = ("sede", "campeon", "mvp_mundial", "maximo_goleador")
    fieldsets = (
        ("Información General", {"fields": ("anio", "nombre", "sede", "descripcion")}),
        ("Imágenes", {"fields": ("imagen_logo", "imagen_portada")}),
        ("Cuadro de Honor (Podio)", {"fields": ("campeon", "subcampeon", "tercer_puesto")}),
        ("Premios Individuales", {"fields": (
            "maximo_goleador", "goles_maximo_goleador", "mvp_mundial", "mejor_arquero"
        )}),
    )
    inlines = [PosicionGrupoInline, PartidoEliminatoriaInline]

    @admin.display(description="Logo")
    def mostrar_logo(self, obj):
        if obj.imagen_logo:
            return format_html(
                '<img src="{}" width="40" height="40" '
                'style="object-fit:contain; border-radius:4px;" />',
                obj.imagen_logo.url,
            )
        return "Sin Logo"
