
from django.urls import path

from . import views

urlpatterns = [
    path("rutinas/nueva/", views.crear_rutina, name="crear_rutina"),
    path("rutinas/<int:pk>/editar/", views.editar_rutina, name="editar_rutina"),
    path("rutinas/<int:pk>/eliminar/", views.eliminar_rutina, name="eliminar_rutina"),
    path("", views.portada, name="home"),
    path("rutinas/", views.lista_rutinas, name="lista_rutinas"),
    path("rutinas/<int:pk>/", views.detalle_rutina, name="detalle_rutina"),
    path("cuentas/registro/", views.registro, name="registro"),
    path("cuentas/login/", views.IngresoView.as_view(), name="login"),
    path("cuentas/logout/", views.SalirView.as_view(), name="logout"),
    path("cuentas/mi-cuenta/", views.cuenta, name="cuenta"),
    path("cuentas/mi-cuenta/editar/", views.editar_perfil, name="editar_perfil"),
    path("cuentas/mi-cuenta/password/", views.CambiarPasswordView.as_view(), name="cambiar_password"),
    path("mis-rutinas/", views.mis_rutinas, name="mis_rutinas"),
]