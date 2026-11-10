
from django.shortcuts import render

from .models import Disciplina, Inscripcion, Rutina


def portada(request):
    recientes = (
        Rutina.objects
        .select_related("disciplina", "entrenador")   # evita N+1 en las tarjetas
        .order_by("-fecha_creacion")[:4]
    )
    contexto = {
        "recientes": recientes,
        "total_rutinas": Rutina.objects.count(),
        "total_disciplinas": Disciplina.objects.count(),
        "total_confirmadas": Inscripcion.objects.filter(
            estado=Inscripcion.Estado.CONFIRMADA
        ).count(),
    }
    return render(request, "rutinas/portada.html", contexto)

