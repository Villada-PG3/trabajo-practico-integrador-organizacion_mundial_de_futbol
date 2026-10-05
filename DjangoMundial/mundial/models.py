from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Mundial(models.Model):
    anio = models.IntegerField(verbose_name="Año")
    sede = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Mundial"
        verbose_name_plural = "Mundiales"

    def __str__(self):
        return f"Copa Mundial {self.sede} {self.anio}"


class Seleccion(models.Model):
    nombre = models.CharField(max_length=100)
    confederacion = models.CharField(max_length=50, help_text="Ej: CONMEBOL, UEFA")
    titulos = models.PositiveIntegerField(default=0, verbose_name="Títulos Mundiales")
    mundial = models.ForeignKey(
        Mundial, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="selecciones"
    )

    class Meta:
        verbose_name = "Selección"
        verbose_name_plural = "Selecciones"

    def __str__(self):
        return self.nombre


class Jugador(models.Model):

    POSICIONES = [
        ("ARQ", "Arquero"),
        ("DEF", "Defensa"),
        ("MED", "Mediocampista"),
        ("DEL", "Delantero"),
    ]

    apellido_nombres = models.CharField(
        max_length=150,
        verbose_name="Apellido y nombres"
    )

    pasaporte = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Número de pasaporte"
    )

    edad = models.PositiveIntegerField(
        validators=[
            MinValueValidator(15),
            MaxValueValidator(50)
        ]
    )

    posicion = models.CharField(
        max_length=3,
        choices=POSICIONES
    )

    equipo_actual = models.CharField(
        max_length=100,
        verbose_name="Equipo actual"
    )

    pais_equipo = models.CharField(
        max_length=100,
        verbose_name="País del equipo"
    )

    numero_camiseta = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(99)
        ],
        verbose_name="Número de camiseta"
    )

    seleccion = models.ForeignKey(
        Seleccion,
        on_delete=models.CASCADE,
        related_name="jugadores"
    )

    class Meta:
        verbose_name = "Jugador"
        verbose_name_plural = "Jugadores"

    def __str__(self):
        return f"{self.apellido_nombres} ({self.seleccion.nombre})"

    class Meta:
        verbose_name = "Jugador"
        verbose_name_plural = "Jugadores"

    def __str__(self):
        return f"{self.apellido_nombres} ({self.seleccion.nombre})"

    class Meta:
        verbose_name = "Jugador"
        verbose_name_plural = "Jugadores"

    def __str__(self):
        return f"{self.apellido_nombres} ({self.seleccion.nombre})"