
from django.db import connection
from django.test.utils import CaptureQueriesContext

from rutinas.models import Rutina

with CaptureQueriesContext(connection) as sin:
    for r in Rutina.objects.all()[:5]:
        r.disciplina
        r.entrenador
        list(r.equipamiento.all())

print("SIN optimizar:", len(sin), "consultas")

with CaptureQueriesContext(connection) as con:
    qs = (Rutina.objects
          .select_related("disciplina", "entrenador")
          .prefetch_related("equipamiento")[:5])
    for r in qs:
        r.disciplina
        r.entrenador
        list(r.equipamiento.all())

print("CON optimizar:", len(con), "consultas")