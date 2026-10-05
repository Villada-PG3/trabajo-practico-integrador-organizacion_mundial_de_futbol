from django.contrib import admin
from .models import Mundial, Seleccion, Jugador

admin.site.register(Mundial)
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