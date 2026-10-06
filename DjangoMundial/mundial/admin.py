from django.contrib import admin
from .models import Mundial, Seleccion, Jugador
from django.utils.html import format_html


admin.site.register(Seleccion)
admin.site.register(Jugador)
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

    def mostrar_logo(self, obj):
        if obj.imagen_logo:
            return format_html('<img src="{}" width="40" height="40" style="object-fit:contain; border-radius:4px;" />', obj.imagen_logo.url)
        return "Sin Logo"
    mostrar_logo.short_description = "Logo"
