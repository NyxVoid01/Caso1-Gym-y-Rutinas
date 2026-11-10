
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DisciplinaForm, PerfilForm, RegistroForm, RutinaForm
from .models import Disciplina, Inscripcion, Rutina
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.db.models import Count


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

# ---------- CRUD de rutinas ----------
def obtener_rutina_propia(request, pk):
    """Devuelve la rutina solo si pertenece al usuario; si no, 403."""
    rutina = get_object_or_404(Rutina, pk=pk)
    if rutina.entrenador != request.user:
        raise PermissionDenied("Solo el entrenador que publicó esta rutina puede modificarla.")
    return rutina 

@login_required
def crear_rutina(request):
    if request.method == "POST":
        form = RutinaForm(request.POST, entrenador=request.user)
        if form.is_valid():
            rutina = form.save(commit=False)     # 1) objeto en memoria, aún sin guardar
            rutina.entrenador = request.user     # 2) el dueño lo pone el servidor, no el usuario
            rutina.save()                        # 3) ahora sí se guarda en MySQL
            form.save_m2m()                      # 4) guarda el equipamiento (tabla intermedia)
            messages.success(request, f"Rutina «{rutina.titulo}» publicada.")
            return redirect("detalle_rutina", pk=rutina.pk)
        messages.error(request, "No se pudo publicar la rutina. Revisa los errores.")
    else:
        form = RutinaForm(entrenador=request.user)
    return render(request, "rutinas/form.html", {"form": form, "titulo_pagina": "Publicar rutina"})


@login_required
def editar_rutina(request, pk):
    rutina = obtener_rutina_propia(request, pk)
    # (Hito 4: aquí agregaremos el bloqueo si no eres el dueño)
    if request.method == "POST":
        form = RutinaForm(request.POST, instance=rutina, entrenador=rutina.entrenador)
        if form.is_valid():
            form.save()
            messages.success(request, "Cambios guardados.")
            return redirect("detalle_rutina", pk=rutina.pk)
        messages.error(request, "No se pudieron guardar los cambios. Revisa los errores.")
    else:
        form = RutinaForm(instance=rutina, entrenador=rutina.entrenador)   # precarga los datos
    return render(request, "rutinas/form.html", {
        "form": form, "rutina": rutina, "titulo_pagina": f"Editar «{rutina.titulo}»"})


@login_required
def eliminar_rutina(request, pk):
    rutina = obtener_rutina_propia(request, pk)
    # (Hito 4: aquí agregaremos el bloqueo si no eres el dueño)
    if request.method == "POST":                 # solo se borra al CONFIRMAR (POST)
        titulo = rutina.titulo
        rutina.delete()
        messages.success(request, f"Rutina «{titulo}» eliminada.")
        return redirect("lista_rutinas")
    # GET: mostramos la pantalla de confirmación
    return render(request, "rutinas/confirmar_eliminar.html", {
        "rutina": rutina,
        "total_inscripciones": rutina.inscripciones.count(),
    })

@login_required
def mis_rutinas(request):
    rutinas = (
        request.user.rutinas                       # solo las mías (related_name)
        .select_related("disciplina")
        .prefetch_related("equipamiento")
        .annotate(
            total_inscritos=Count("inscripciones"),
            pendientes=Count("inscripciones", filter=Q(inscripciones__estado="pendiente")),
        )
        .order_by("-fecha_creacion", "-id")
    )
    return render(request, "rutinas/mis_rutinas.html", {"rutinas": rutinas})

# ---------- Catálogo: disciplinas ----------

@login_required
def disciplinas(request):
    if request.method == "POST":
        form = DisciplinaForm(request.POST)
        if form.is_valid():
            disciplina = form.save()
            messages.success(request, f"Disciplina «{disciplina.nombre}» creada.")
            return redirect("disciplinas")
        messages.error(request, "No se pudo crear la disciplina.")
    else:
        form = DisciplinaForm()

    lista = Disciplina.objects.annotate(total_rutinas=Count("rutinas")).order_by("nombre")
    return render(request, "rutinas/disciplinas.html", {"form": form, "disciplinas": lista})


@login_required
def eliminar_disciplina(request, pk):
    # El catálogo es compartido: si lo borra cualquiera, afecta rutinas ajenas.
    if not request.user.is_staff:
        raise PermissionDenied("Solo el personal del gimnasio puede eliminar disciplinas.")

    disciplina = get_object_or_404(Disciplina, pk=pk)
    afectadas = disciplina.rutinas.count()

    if request.method == "POST":
        nombre = disciplina.nombre
        disciplina.delete()          # on_delete=SET_NULL: las rutinas quedan "sin disciplina"
        messages.success(
            request,
            f"Disciplina «{nombre}» eliminada. {afectadas} rutina(s) quedaron sin disciplina.",
        )
        return redirect("disciplinas")

    return render(request, "rutinas/confirmar_eliminar_disciplina.html", {
        "disciplina": disciplina, "afectadas": afectadas,
    })