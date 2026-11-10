from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Disciplina(models.Model):
    """Catálogo (uno a muchos con Rutina): funcional, yoga, spinning..."""
    nombre = models.CharField("nombre", max_length=60, unique=True)

    class Meta:
        verbose_name = "disciplina"
        verbose_name_plural = "disciplinas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Equipamiento(models.Model):
    """Etiqueta (muchos a muchos con Rutina): mancuernas, banco, colchoneta..."""
    nombre = models.CharField("nombre", max_length=60, unique=True)

    class Meta:
        verbose_name = "equipamiento"
        verbose_name_plural = "equipamientos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Rutina(models.Model):
    """Entidad principal. Su dueño es el entrenador que la publica."""

    class Nivel(models.TextChoices):
        BASICO = "basico", "Básico"
        INTERMEDIO = "intermedio", "Intermedio"
        AVANZADO = "avanzado", "Avanzado"

    titulo = models.CharField("título", max_length=100)
    descripcion = models.TextField("descripción")
    duracion_minutos = models.PositiveSmallIntegerField(
        "duración (minutos)",
        validators=[MinValueValidator(10), MaxValueValidator(120)],
    )
    cupos = models.PositiveSmallIntegerField(
        "cupos",
        validators=[MinValueValidator(1), MaxValueValidator(30)],
    )
    nivel = models.CharField(
        "nivel", max_length=12, choices=Nivel.choices, default=Nivel.BASICO
    )
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)

    entrenador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rutinas",
        verbose_name="entrenador",
    )
    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rutinas",
        verbose_name="disciplina",
    )
    equipamiento = models.ManyToManyField(
        Equipamiento,
        blank=True,
        related_name="rutinas",
        verbose_name="equipamiento",
    )

    class Meta:
        verbose_name = "rutina"
        verbose_name_plural = "rutinas"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return self.titulo


class Inscripcion(models.Model):
    """Solicitud: une a dos usuarios (el socio que la crea y el entrenador dueño de la rutina)."""

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        CONFIRMADA = "confirmada", "Confirmada"
        RECHAZADA = "rechazada", "Rechazada"

    rutina = models.ForeignKey(
        Rutina,
        on_delete=models.CASCADE,
        related_name="inscripciones",
        verbose_name="rutina",
    )
    socio = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inscripciones",
        verbose_name="socio",
    )
    comentario = models.TextField("comentario", blank=True)
    fecha = models.DateTimeField("fecha", auto_now_add=True)
    estado = models.CharField(
        "estado", max_length=12, choices=Estado.choices, default=Estado.PENDIENTE
    )

    class Meta:
        verbose_name = "inscripción"
        verbose_name_plural = "inscripciones"
        ordering = ["-fecha"]
        constraints = [
            models.UniqueConstraint(
                fields=["rutina", "socio"], name="inscripcion_unica_por_socio"
            )
        ]

    def clean(self):
        # Regla del caso: un socio no puede inscribirse en una rutina propia.
        if self.rutina_id and self.socio_id and self.rutina.entrenador_id == self.socio_id:
            raise ValidationError("No puedes inscribirte en una rutina que tú publicaste.")

    def __str__(self):
        return f"{self.socio} → {self.rutina} ({self.get_estado_display()})"