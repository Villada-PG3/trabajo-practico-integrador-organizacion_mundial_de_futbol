from django.contrib import admin
from django.utils.html import format_html
from .models import Mundial, Seleccion, Jugador, PosicionGrupo, PartidoEliminatoria
from .models import Mundial, Seleccion, Jugador, PosicionGrupo, PartidoEliminatoria, HistorialJugador

# Registro de Selección
admin.site.register(Seleccion)


# Registro de Jugador con su clase personalizada
@admin.register(Jugador)
class JugadorAdmin(admin.ModelAdmin):
    list_display = (
        "apellido_nombres",
        "pasaporte",
        "edad",
        "posicion",
        "equipo_actual",
        "pais_equipo",
        "numero_camiseta",
        "seleccion",
    )

    search_fields = (
        "apellido_nombres",
        "pasaporte",
        "equipo_actual",
    )

    list_filter = (
        "posicion",
        "seleccion",
    )

@admin.register(HistorialJugador)
class HistorialJugadorAdmin(admin.ModelAdmin):
    list_display = (
        "jugador",
        "mundial",
        "partidos_jugados",
        "goles",
    )

    list_filter = ("mundial",)

    search_fields = (
        "jugador__apellido_nombres",
    )

    ordering = ("-mundial__anio",)


# Inlines para cargar las Posiciones de Grupos y los Partidos de Eliminatorias dentro del mismo Mundial
class PosicionGrupoInline(admin.TabularInline):
    model = PosicionGrupo
    extra = 4  # Carga 4 filas por defecto para completar rápido un grupo
    fields = ('grupo', 'equipo', 'pts', 'pj', 'gf', 'gc', 'g', 'e', 'p', 'forma')


class PartidoEliminatoriaInline(admin.TabularInline):
    model = PartidoEliminatoria
    extra = 2  # Carga 2 filas por defecto para agregar partidos
    fields = ('fase', 'equipo1', 'goles1', 'equipo2', 'goles2', 'info_extra')


# Registro de Mundial con Inlines y todas tus configuraciones originales
@admin.register(Mundial)
class MundialAdmin(admin.ModelAdmin):
    list_display = ('anio', 'sede', 'campeon', 'mvp_mundial', 'maximo_goleador', 'mostrar_logo')
    list_filter = ('anio', 'sede')
    search_fields = ('sede', 'campeon', 'mvp_mundial', 'maximo_goleador')
    
    fieldsets = (
        ('Información General', {
            'fields': ('anio', 'sede', 'descripcion')
        }),
        ('Imágenes', {
            'fields': ('imagen_logo', 'imagen_portada')
        }),
        ('Cuadro de Honor (Podio)', {
            'fields': ('campeon', 'subcampeon', 'tercer_puesto')
        }),
        ('Premios Individuales', {
            'fields': ('maximo_goleador', 'goles_maximo_goleador', 'mvp_mundial', 'mejor_arquero')
        }),
    )

    # Agregamos los Inlines al final del formulario de Mundial
    inlines = [PosicionGrupoInline, PartidoEliminatoriaInline]

    def mostrar_logo(self, obj):
        if obj.imagen_logo:
            return format_html('<img src="{}" width="40" height="40" style="object-fit:contain; border-radius:4px;" />', obj.imagen_logo.url)
        return "Sin Logo"
    mostrar_logo.short_description = "Logo"