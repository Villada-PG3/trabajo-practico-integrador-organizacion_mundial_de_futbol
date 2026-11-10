from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# ==========================================
# MUNDIAL

# ==========================================

class Mundial(models.Model):
    anio = models.IntegerField(
        unique=True,
        verbose_name="Año"
    )
    nombre = models.CharField(
        max_length=100,
        default="Copa Mundial de Fútbol",
        verbose_name="Nombre"
    )
    sede = models.CharField(
        max_length=100,
        verbose_name="Sede"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción"
    )
    # Cuadro de Honor
    campeon = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Campeón"
    )
    subcampeon = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Subcampeón"
    )
    tercer_puesto = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Tercer Puesto"
    )
    # Premios Individuales
    maximo_goleador = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Máximo Goleador"
    )
    goles_maximo_goleador = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        verbose_name="Goles del Máximo Goleador"
    )
    mvp_mundial = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="MVP / Mejor Jugador"
    )
    mejor_arquero = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Mejor Arquero"
    )
    # Imágenes
    imagen_logo = models.ImageField(
        upload_to="mundiales/logos/",
        blank=True,
        null=True,
        verbose_name="Logo / Emblema"
    )
    imagen_portada = models.ImageField(
        upload_to="mundiales/portadas/",
        blank=True,
        null=True,
        verbose_name="Imagen de Portada"
    )

    class Meta:
        verbose_name = "Mundial"
        verbose_name_plural = "Mundiales"
        ordering = ["-anio"]

    def __str__(self):
        return f"Copa Mundial {self.anio} - {self.sede}"

# ==========================================
# POSICIONES DE GRUPOS

# ==========================================

class PosicionGrupo(models.Model):
    GRUPOS_CHOICES = [
        (f"Grupo {letra}", f"Grupo {letra}")
        for letra in "ABCDEFGHIJKL"
    ]
    mundial = models.ForeignKey(
        Mundial,
        on_delete=models.CASCADE,
        related_name="posiciones"
    )
    grupo = models.CharField(
        max_length=10,
        choices=GRUPOS_CHOICES,
        default="Grupo A"
    )
    equipo = models.CharField(
        max_length=50
    )
    pj = models.PositiveIntegerField(
        default=0,
        verbose_name="J (Jugados)"
    )
    g = models.PositiveIntegerField(
        default=0,
        verbose_name="G (Ganados)"
    )
    e = models.PositiveIntegerField(
        default=0,
        verbose_name="E (Empatados)"
    )
    p = models.PositiveIntegerField(
        default=0,
        verbose_name="P (Perdidos)"
    )
    gf = models.PositiveIntegerField(
        default=0,
        verbose_name="GF (Goles Favor)"
    )
    gc = models.PositiveIntegerField(
        default=0,
        verbose_name="GC (Goles Contra)"
    )
    pts = models.PositiveIntegerField(
        default=0,
        verbose_name="PTS (Puntos)"
    )
    forma = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Ejemplo: V,V,V o V,E,D"
    )

    class Meta:
        ordering = ["grupo", "-pts", "-g", "-gf"]
        verbose_name = "Posición de Grupo"
        verbose_name_plural = "Posiciones de Grupos"

    @property

    def diferencia_gol(self):
        return self.gf - self.gc

    @property

    def lista_forma(self):
        if self.forma:
            return [
                f.strip().upper()
                for f in self.forma.split(",")
            ]
        return []

    def __str__(self):
        return f"{self.grupo} - {self.equipo} ({self.pts} pts)"

# ==========================================
# PARTIDOS DE ELIMINATORIAS

# ==========================================

class PartidoEliminatoria(models.Model):
    FASE_CHOICES = [
        ("16vos", "16vos de Final"),
        ("Octavos", "Octavos de Final"),
        ("Cuartos", "Cuartos de Final"),
        ("Semifinal", "Semifinales"),
        ("Tercer Puesto", "Tercer Puesto"),
        ("Final", "Gran Final"),
    ]
    mundial = models.ForeignKey(
        Mundial,
        on_delete=models.CASCADE,
        related_name="partidos_eliminatoria"
    )
    fase = models.CharField(
        max_length=20,
        choices=FASE_CHOICES,
        default="Octavos"
    )
    # NUEVO: Orden de los partidos dentro del cuadro
    orden = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden en el cuadro",
        help_text="Determina la posición del partido dentro de su fase"
    )
    equipo1 = models.CharField(
        max_length=50,
        verbose_name="Equipo 1"
    )
    goles1 = models.PositiveIntegerField(
        default=0,
        verbose_name="Goles Equipo 1"
    )
    equipo2 = models.CharField(
        max_length=50,
        verbose_name="Equipo 2"
    )
    goles2 = models.PositiveIntegerField(
        default=0,
        verbose_name="Goles Equipo 2"
    )
    info_extra = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Ej: Penales 4-3, 18/06 16:00"
    )

    class Meta:
        verbose_name = "Partido de Eliminatoria"
        verbose_name_plural = "Partidos de Eliminatorias"
        ordering = ["orden", "id"]

    def __str__(self):
        return (
            f"{self.get_fase_display()}: "
            f"{self.equipo1} ({self.goles1}) vs "
            f"({self.goles2}) {self.equipo2}"
        )

class Confederacion(models.Model):
    NOMBRE_CHOICES = [
        ('CONMEBOL', 'CONMEBOL (Sudamérica)'),
        ('UEFA', 'UEFA (Europa)'),
        ('CONCACAF', 'CONCACAF (Norte/Centroamérica)'),
        ('CAF', 'CAF (África)'),
        ('AFC', 'AFC (Asia)'),
        ('OFC', 'OFC (Oceanía)'),
    ]
    nombre = models.CharField(max_length=20, choices=NOMBRE_CHOICES, unique=True)

    def __str__(self):
        return self.get_nombre_display()

class Seleccion(models.Model):
    nombre = models.CharField(max_length=100)
    confederacion = models.ForeignKey(
        Confederacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="selecciones",
    )

    @property
    def bandera_url(self):
        codigos = {
            "argentina": "ar",
            "brasil": "br",
            "alemania": "de",
            "españa": "es",
            "francia": "fr",
            "inglaterra": "gb-eng",
            "portugal": "pt",
            "uruguay": "uy",
            "méxico": "mx",
            "estados unidos": "us",
            "japón": "jp",
            "corea del sur": "kr",
            "marruecos": "ma",
            "senegal": "sn",
            "croacia": "hr",
            "países bajos": "nl",
            "bélgica": "be",
            "suiza": "ch",
            "canadá": "ca",
            "australia": "au",
            "costa rica": "cr",
            "ecuador": "ec",
            "colombia": "co",
            "chile": "cl",
            "paraguay": "py",
            "perú": "pe",
            "arabia saudita": "sa",
            "qatar": "qa",
            "camerún": "cm",
            "ghana": "gh",
            "túnez": "tn",
            "egipto": "eg",
            "nigeria": "ng",
            "serbia": "rs",
            "dinamarca": "dk",
            "polonia": "pl",
            "gales": "gb-wls",
            "escocia": "gb-sct",
            "irán": "ir",
        }
        codigo = codigos.get(self.nombre.strip().lower())
        if codigo:
            return f"https://flagcdn.com/w160/{codigo}.png"
        return None

    class Meta:
        verbose_name = "Selección"
        verbose_name_plural = "Selecciones"

    def __str__(self):
        return self.nombre

class PersonalTecnico(models.Model):
    FUNCIONES = [
        ('DT', 'Director Técnico'),
        ('PF', 'Preparador Físico'),
        ('EA', 'Entrenador de Arqueros'),
        ('MED', 'Médico'),
        ('AUM', 'Auxiliar/Otro'),
    ]
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    pasaporte = models.CharField(max_length=50, unique=True)
    funcion = models.CharField(max_length=10, choices=FUNCIONES)
    seleccion = models.ForeignKey(Seleccion, on_delete=models.CASCADE, related_name='plantel_tecnico')
    mundial = models.ForeignKey(
        Mundial, on_delete=models.CASCADE, null=True, blank=True,
        related_name='planteles_tecnicos',
        verbose_name='Mundial de participación',
        help_text='Obligatorio al crear desde el panel de una edición.'
    )

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.get_funcion_display()})"

# ==========================================
# JUGADORES

# ==========================================

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
        return (
            f"{self.apellido_nombres} "
            f"({self.seleccion.nombre})"
        )

# ==========================================
# HISTORIAL DE JUGADORES

# ==========================================

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
    asistencias = models.PositiveIntegerField(
        default=0,
        verbose_name="Asistencias"
    )
    numero_camiseta_mundial = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(99)],
        verbose_name="Dorsal en este Mundial"
    )

    class Meta:
        verbose_name = "Historial de jugador"
        verbose_name_plural = "Historiales de jugadores"
        ordering = [
            "-mundial__anio",
            "jugador__apellido_nombres"
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["jugador", "mundial"],
                name="un_historial_por_jugador_y_mundial"
            )
        ]

    def __str__(self):
        return (
            f"{self.jugador.apellido_nombres} - "
            f"{self.mundial.anio}"
        )

# ==========================================
# EVENTOS DE LOS PARTIDOS

# ==========================================

class EventoPartido(models.Model):
    TIPOS_EVENTO = [
        ("GOL", "Gol"),
        ("PENAL", "Gol de penal"),
        ("AUTOGOL", "Gol en contra"),
        ("AMARILLA", "Tarjeta amarilla"),
        ("ROJA", "Tarjeta roja"),
        ("DOBLE_AMARILLA", "Expulsión por doble amarilla"),
        ("CAMBIO", "Cambio de jugador"),
        ("FALTA", "Falta"),
        ("INICIO", "Inicio del partido"),
        ("DESCANSO", "Descanso"),
        ("FINAL", "Final del partido"),
    ]
    partido = models.ForeignKey(
        PartidoEliminatoria,
        on_delete=models.CASCADE,
        related_name="eventos",
        verbose_name="Partido"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPOS_EVENTO,
        verbose_name="Tipo de evento"
    )
    minuto = models.CharField(
        max_length=10,
        verbose_name="Minuto",
        help_text="Ejemplo: 34, 45+2, 90+7"
    )
    equipo = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Selección"
    )
    jugador = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Jugador"
    )
    jugador_entra = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Jugador que entra"
    )
    jugador_sale = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Jugador que sale"
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción"
    )

    class Meta:
        verbose_name = "Evento del partido"
        verbose_name_plural = "Eventos de los partidos"
        ordering = ["id"]

    def __str__(self):
        return (
            f"{self.get_tipo_display()} - "
            f"{self.minuto}' - {self.jugador}"
        )

class PartidoMundial2022(models.Model):
    mundial = models.ForeignKey(
        'Mundial',
        on_delete=models.CASCADE,
        related_name='partidos_2022'
    )
    equipo1 = models.ForeignKey(
        'Seleccion',
        on_delete=models.PROTECT,
        related_name='partidos_2022_equipo1'
    )
    equipo2 = models.ForeignKey(
        'Seleccion',
        on_delete=models.PROTECT,
        related_name='partidos_2022_equipo2'
    )
    fifa_match_id = models.BigIntegerField(unique=True)
    fecha = models.DateField()
    hora_local = models.CharField(max_length=5, blank=True)
    fase = models.CharField(max_length=30)
    grupo = models.CharField(max_length=20, blank=True)
    goles1 = models.PositiveSmallIntegerField(default=0)
    goles2 = models.PositiveSmallIntegerField(default=0)
    penales1 = models.PositiveSmallIntegerField(default=0)
    penales2 = models.PositiveSmallIntegerField(default=0)
    estadio = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ['fecha', 'fifa_match_id']
        verbose_name = 'Partido del Mundial 2022'
        verbose_name_plural = 'Partidos del Mundial 2022'

    def __str__(self):
        return (
            f'{self.equipo1.nombre} '
            f'{self.goles1}-{self.goles2} '
            f'{self.equipo2.nombre}'
        )
# Participación explícita de una selección por edición.
class ParticipacionSeleccion(models.Model):
    mundial = models.ForeignKey(Mundial, on_delete=models.CASCADE, related_name="selecciones_participantes")
    seleccion = models.ForeignKey(Seleccion, on_delete=models.PROTECT, related_name="mundiales_disputados")
    instancia_alcanzada = models.CharField(max_length=60, blank=True, verbose_name="Instancia alcanzada")
    observaciones = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["mundial", "seleccion"], name="unica_seleccion_por_mundial")]
        ordering = ["seleccion__nombre"]
        verbose_name = "Selección participante"
        verbose_name_plural = "Selecciones participantes"

    def __str__(self):
        return f"{self.seleccion.nombre} · {self.mundial.anio}"
# Partidos de grupos para nuevas ediciones, sin tocar los 64 partidos históricos de Qatar.
class PartidoGrupo(models.Model):
    mundial = models.ForeignKey(Mundial, on_delete=models.CASCADE, related_name="partidos_grupo")
    grupo = models.CharField(max_length=20, choices=PosicionGrupo.GRUPOS_CHOICES)
    fecha = models.DateField(null=True, blank=True)
    estadio = models.CharField(max_length=150, blank=True)
    equipo1 = models.ForeignKey(Seleccion, on_delete=models.PROTECT, related_name="partidos_grupo_local")
    equipo2 = models.ForeignKey(Seleccion, on_delete=models.PROTECT, related_name="partidos_grupo_visitante")
    goles1 = models.PositiveSmallIntegerField(default=0)
    goles2 = models.PositiveSmallIntegerField(default=0)
    jugado = models.BooleanField(default=False, verbose_name="Partido disputado", help_text="Activar cuando el resultado sea definitivo; permite distinguir 0-0 de un partido pendiente.")
    corners1 = models.PositiveSmallIntegerField(default=0, verbose_name="Córners equipo 1")
    corners2 = models.PositiveSmallIntegerField(default=0, verbose_name="Córners equipo 2")
    laterales1 = models.PositiveSmallIntegerField(default=0, verbose_name="Laterales equipo 1")
    laterales2 = models.PositiveSmallIntegerField(default=0, verbose_name="Laterales equipo 2")
    faltas1 = models.PositiveSmallIntegerField(default=0, verbose_name="Faltas equipo 1")
    faltas2 = models.PositiveSmallIntegerField(default=0, verbose_name="Faltas equipo 2")
    minutos_ataque1 = models.PositiveSmallIntegerField(default=0, verbose_name="Minutos de ataque equipo 1")
    minutos_ataque2 = models.PositiveSmallIntegerField(default=0, verbose_name="Minutos de ataque equipo 2")

    class Meta:
        ordering = ["fecha", "pk"]
        verbose_name = "Partido de grupos"
        verbose_name_plural = "Partidos de grupos"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.equipo1_id and self.equipo1_id == self.equipo2_id:
            raise ValidationError("Los equipos deben ser diferentes.")

    def __str__(self):
        return f"{self.mundial.anio}: {self.equipo1} {self.goles1}-{self.goles2} {self.equipo2}"

class EstadisticaJugadorPartido(models.Model):
    mundial = models.ForeignKey(Mundial, on_delete=models.CASCADE, related_name="estadisticas_por_partido")
    jugador = models.ForeignKey(Jugador, on_delete=models.PROTECT, related_name="estadisticas_por_partido")
    partido_grupo = models.ForeignKey(PartidoGrupo, on_delete=models.CASCADE, blank=True, null=True, related_name="estadisticas_jugadores")
    partido_eliminatoria = models.ForeignKey(PartidoEliminatoria, on_delete=models.CASCADE, blank=True, null=True, related_name="estadisticas_jugadores")
    goles = models.PositiveSmallIntegerField(default=0)
    asistencias = models.PositiveSmallIntegerField(default=0)
    faltas = models.PositiveSmallIntegerField(default=0)
    amarillas = models.PositiveSmallIntegerField(default=0)
    rojas = models.PositiveSmallIntegerField(default=0)
    minutos_jugados = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Estadística individual por partido"
        verbose_name_plural = "Estadísticas individuales por partido"

    def clean(self):
        from django.core.exceptions import ValidationError
        if bool(self.partido_grupo_id) == bool(self.partido_eliminatoria_id):
            raise ValidationError("Seleccioná exactamente un partido (de grupos o eliminatoria).")
        partido = self.partido_grupo or self.partido_eliminatoria
        if partido and self.mundial_id and partido.mundial_id != self.mundial_id:
            raise ValidationError("El partido debe pertenecer al Mundial seleccionado.")
        if self.jugador_id and self.mundial_id and not HistorialJugador.objects.filter(jugador_id=self.jugador_id, mundial_id=self.mundial_id).exists():
            raise ValidationError("El jugador no está asociado a este Mundial.")

    def __str__(self):
        return f"{self.jugador} · {self.mundial.anio}"

class EventoGrupo(models.Model):
    """Evento asociado a un partido de grupos actual o al archivo histórico de Qatar."""
    TIPOS_EVENTO = EventoPartido.TIPOS_EVENTO
    partido_grupo = models.ForeignKey(PartidoGrupo, on_delete=models.CASCADE, null=True, blank=True, related_name="eventos_grupo", verbose_name="Partido de grupos")
    partido_qatar = models.ForeignKey(PartidoMundial2022, on_delete=models.CASCADE, null=True, blank=True, related_name="eventos_grupo", verbose_name="Partido histórico Qatar 2022")
    tipo = models.CharField(max_length=20, choices=TIPOS_EVENTO)
    minuto = models.CharField(max_length=10, help_text="Ejemplo: 34 o 45+2")
    equipo = models.CharField(max_length=100, blank=True)
    jugador = models.CharField(max_length=150, blank=True)
    jugador_entra = models.CharField(max_length=150, blank=True)
    jugador_sale = models.CharField(max_length=150, blank=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Evento de partido de grupos"
        verbose_name_plural = "Eventos de partidos de grupos"
        ordering = ["pk"]

    def clean(self):
        from django.core.exceptions import ValidationError
        if bool(self.partido_grupo_id) == bool(self.partido_qatar_id):
            raise ValidationError("Seleccioná exactamente un partido: de grupos o de Qatar 2022.")
        if self.partido_qatar_id and not self.partido_qatar.grupo:
            raise ValidationError("El encuentro histórico debe ser de fase de grupos.")

    def __str__(self):
        return f"{self.minuto}' · {self.get_tipo_display()} · {self.jugador or self.equipo}"
