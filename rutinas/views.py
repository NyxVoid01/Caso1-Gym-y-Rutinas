
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PerfilForm, RegistroForm
from .models import Disciplina, Inscripcion, Rutina
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy


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

def lista_rutinas(request):
    q = request.GET.get("q", "").strip()
    disciplina = request.GET.get("disciplina", "")

    rutinas = (
        Rutina.objects
        .select_related("disciplina", "entrenador")   # FK → JOIN
        .prefetch_related("equipamiento")             # M2M → 1 consulta extra para todas
        .order_by("-fecha_creacion", "-id")           # orden estable: no repite ni pierde filas
    )

    # Búsqueda en dos campos
    if q:
        rutinas = rutinas.filter(Q(titulo__icontains=q) | Q(descripcion__icontains=q))

    # Filtro por catálogo (también "sin disciplina", porque es opcional)
    if disciplina.isdigit():
        rutinas = rutinas.filter(disciplina_id=disciplina)
    elif disciplina == "sin":
        rutinas = rutinas.filter(disciplina__isnull=True)

    # Paginación de a 5
    paginator = Paginator(rutinas, 5)
    page_obj = paginator.get_page(request.GET.get("page"))   # tolera ?page=999 o ?page=abc

    # Conservar búsqueda y filtro al cambiar de página
    params = request.GET.copy()
    params.pop("page", None)

    return render(request, "rutinas/lista.html", {
        "page_obj": page_obj,
        "disciplinas": Disciplina.objects.all(),
        "q": q,
        "disciplina_actual": disciplina,
        "querystring": params.urlencode(),
    })


def detalle_rutina(request, pk):
    rutina = get_object_or_404(
        Rutina.objects
        .select_related("disciplina", "entrenador")
        .prefetch_related("equipamiento"),
        pk=pk,
    )
    confirmadas = rutina.inscripciones.filter(estado=Inscripcion.Estado.CONFIRMADA).count()
    return render(request, "rutinas/detalle.html", {
        "rutina": rutina,
        "confirmadas": confirmadas,
        "cupos_disponibles": max(rutina.cupos - confirmadas, 0),
    })

# ---------- Cuentas ----------

def registro(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":                 # se ENVIÓ el formulario
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()                   # crea el usuario con la clave hasheada
            login(request, user)                 # y deja la sesión iniciada
            messages.success(request, f"¡Bienvenido/a, {user.username}! Tu cuenta fue creada.")
            return redirect("home")
        messages.error(request, "Revisa los errores del formulario.")
    else:                                        # se ABRIÓ el formulario (GET)
        form = RegistroForm()

    return render(request, "registration/registro.html", {"form": form})


class IngresoView(SuccessMessageMixin, LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True
    success_message = "Hola %(username)s, ingresaste correctamente."


class SalirView(LogoutView):
    """LogoutView solo acepta POST (Django 5+): un GET responde 405."""
    next_page = "home"

    def post(self, request, *args, **kwargs):
        respuesta = super().post(request, *args, **kwargs)
        messages.info(request, "Cerraste sesión correctamente.")
        return respuesta

# ---------- Mi cuenta ----------

@login_required
def cuenta(request):
    contexto = {
        "total_rutinas": request.user.rutinas.count(),              # related_name de Rutina.entrenador
        "total_inscripciones": request.user.inscripciones.count(),  # related_name de Inscripcion.socio
        "pendientes_recibidas": Inscripcion.objects.filter(
            rutina__entrenador=request.user,
            estado=Inscripcion.Estado.PENDIENTE,
        ).count(),
    }
    return render(request, "cuentas/cuenta.html", contexto)


@login_required
def editar_perfil(request):
    if request.method == "POST":
        form = PerfilForm(request.POST, instance=request.user)   # edita SOLO al usuario actual
        if form.is_valid():
            form.save()
            messages.success(request, "Tus datos fueron actualizados.")
            return redirect("cuenta")
        messages.error(request, "No se pudieron guardar los cambios. Revisa el formulario.")
    else:
        form = PerfilForm(instance=request.user)                 # precarga los datos actuales
    return render(request, "cuentas/perfil.html", {"form": form})


class CambiarPasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = "cuentas/cambiar_password.html"
    success_url = reverse_lazy("cuenta")
    success_message = "Tu contraseña fue cambiada correctamente."