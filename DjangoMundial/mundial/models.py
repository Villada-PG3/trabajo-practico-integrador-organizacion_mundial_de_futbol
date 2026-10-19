from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Mundial(models.Model):
    anio = models.IntegerField(unique=True, verbose_name="Año")
    nombre = models.CharField(max_length=100, default="Copa Mundial de Fútbol", verbose_name="Nombre")
    sede = models.CharField(max_length=100, verbose_name="Sede")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    # Cuadro de Honor (Podio)
    campeon = models.CharField(max_length=100, blank=True, null=True, verbose_name="Campeón")
    subcampeon = models.CharField(max_length=100, blank=True, null=True, verbose_name="Subcampeón")
    tercer_puesto = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tercer Puesto")

    # Premios Individuales
    maximo_goleador = models.CharField(max_length=100, blank=True, null=True, verbose_name="Máximo Goleador")
    goles_maximo_goleador = models.PositiveIntegerField(default=0, blank=True, null=True, verbose_name="Goles del Máximo Goleador")
    mvp_mundial = models.CharField(max_length=100, blank=True, null=True, verbose_name="MVP / Mejor Jugador")
    mejor_arquero = models.CharField(max_length=100, blank=True, null=True, verbose_name="Mejor Arquero")

    # Imágenes
    imagen_logo = models.ImageField(upload_to='mundiales/logos/', blank=True, null=True, verbose_name="Logo / Emblema")
    imagen_portada = models.ImageField(upload_to='mundiales/portadas/', blank=True, null=True, verbose_name="Imagen de Portada")

    class Meta:
        verbose_name = "Mundial"
        verbose_name_plural = "Mundiales"
        ordering = ['-anio']

    def __str__(self):
        return f"Copa Mundial {self.anio} - {self.sede}"


class PosicionGrupo(models.Model):
    GRUPOS_CHOICES = [
        ('Grupo A', 'Grupo A'),
        ('Grupo B', 'Grupo B'),
        ('Grupo C', 'Grupo C'),
        ('Grupo D', 'Grupo D'),
        ('Grupo E', 'Grupo E'),
        ('Grupo F', 'Grupo F'),
        ('Grupo G', 'Grupo G'),
        ('Grupo H', 'Grupo H'),
    ]
    
    mundial = models.ForeignKey(Mundial, on_delete=models.CASCADE, related_name='posiciones')
    grupo = models.CharField(max_length=10, choices=GRUPOS_CHOICES, default='Grupo A')
    equipo = models.CharField(max_length=50)
    pj = models.PositiveIntegerField(default=0, verbose_name="J (Jugados)")
    g = models.PositiveIntegerField(default=0, verbose_name="G (Ganados)")
    e = models.PositiveIntegerField(default=0, verbose_name="E (Empatados)")
    p = models.PositiveIntegerField(default=0, verbose_name="P (Perdidos)")
    gf = models.PositiveIntegerField(default=0, verbose_name="GF (Goles Favor)")
    gc = models.PositiveIntegerField(default=0, verbose_name="GC (Goles Contra)")
    pts = models.PositiveIntegerField(default=0, verbose_name="PTS (Puntos)")
    forma = models.CharField(max_length=20, blank=True, null=True, help_text="Ejemplo: V,V,V o V,E,D (separados por coma)")

    class Meta:
        ordering = ['grupo', '-pts', '-g', '-gf']
        verbose_name = "Posición de Grupo"
        verbose_name_plural = "Posiciones de Grupos"

    @property
    def diferencia_gol(self):
        return self.gf - self.gc

    @property
    def lista_forma(self):
        if self.forma:
            return [f.strip().upper() for f in self.forma.split(',')]
        return []

    def __str__(self):
        return f"{self.grupo} - {self.equipo} ({self.pts} pts)"


class PartidoEliminatoria(models.Model):
    FASE_CHOICES = [
        ('16vos', '16vos de Final'),
        ('Octavos', 'Octavos de Final'),
        ('Cuartos', 'Cuartos de Final'),
        ('Semifinal', 'Semifinales'),
        ('Final', 'Gran Final'),
    ]

    mundial = models.ForeignKey(Mundial, on_delete=models.CASCADE, related_name='partidos_eliminatoria')
    fase = models.CharField(max_length=20, choices=FASE_CHOICES, default='Octavos')
    equipo1 = models.CharField(max_length=50, verbose_name="Equipo 1")
    goles1 = models.PositiveIntegerField(default=0, verbose_name="Goles Equipo 1")
    equipo2 = models.CharField(max_length=50, verbose_name="Equipo 2")
    goles2 = models.PositiveIntegerField(default=0, verbose_name="Goles Equipo 2")
    info_extra = models.CharField(max_length=50, blank=True, null=True, help_text="Ej: Penales 4-3, 18/06 16:00")

    class Meta:
        verbose_name = "Partido de Eliminatoria"
        verbose_name_plural = "Partidos de Eliminatorias"

    def __str__(self):
        return f"{self.get_fase_display()}: {self.equipo1} ({self.goles1}) vs ({self.goles2}) {self.equipo2}"


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
        return f"{self.apellido_nombres} ({self.seleccion.nombre})"
class HistorialJugador(models.Model):
    jugador = models.ForeignKey(
        Jugador,
        on_delete=models.CASCADE,
        related_name="historiales"
    )

    mundial = models.ForeignKey(
        Mundial,
        on_delete=models.CASCADE,
        related_name="historiales_jugadores"
    )

    partidos_jugados = models.PositiveIntegerField(
        default=0,
        verbose_name="Partidos jugados"
    )

    goles = models.PositiveIntegerField(
        default=0,
        verbose_name="Goles convertidos"
    )

    class Meta:
        verbose_name = "Historial de jugador"
        verbose_name_plural = "Historiales de jugadores"
        ordering = ["-mundial__anio", "jugador__apellido_nombres"]
        constraints = [
            models.UniqueConstraint(
                fields=["jugador", "mundial"],
                name="un_historial_por_jugador_y_mundial"
            )
        ]

    def __str__(self):
        return f"{self.jugador.apellido_nombres} - {self.mundial.anio}"
