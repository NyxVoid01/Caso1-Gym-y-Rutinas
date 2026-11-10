
from django.urls import path

from . import views

urlpatterns = [
    path("", views.portada, name="home"),
    path("rutinas/", views.lista_rutinas, name="lista_rutinas"),
    path("rutinas/<int:pk>/", views.detalle_rutina, name="detalle_rutina"),
    path("cuentas/registro/", views.registro, name="registro"),
    path("cuentas/login/", views.IngresoView.as_view(), name="login"),
    path("cuentas/logout/", views.SalirView.as_view(), name="logout"),
]