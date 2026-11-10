from django.contrib import admin
from .models import Disciplina, Equipamiento, Rutina, Inscripcion


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre"]
    search_fields = ["nombre"]
    list_filter = ["rutinas__nivel"]          # disciplinas que tienen rutinas de cierto nivel


@admin.register(Equipamiento)
class EquipamientoAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre"]
    search_fields = ["nombre"]
    list_filter = ["rutinas__disciplina"]     # equipamiento usado en cierta disciplina


@admin.register(Rutina)
class RutinaAdmin(admin.ModelAdmin):
    list_display = ["titulo", "entrenador", "disciplina", "nivel",
                    "duracion_minutos", "cupos", "fecha_creacion"]
    list_filter = ["nivel", "disciplina", "equipamiento"]
    search_fields = ["titulo", "descripcion", "entrenador__username"]
    filter_horizontal = ["equipamiento"]      # selector cómodo para el ManyToMany
    list_select_related = ["entrenador", "disciplina"]   # evita N+1 en el listado
    date_hierarchy = "fecha_creacion"


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ["socio", "rutina", "estado", "fecha"]
    list_filter = ["estado", "rutina__disciplina"]
    search_fields = ["socio__username", "rutina__titulo", "comentario"]
    list_select_related = ["socio", "rutina"]