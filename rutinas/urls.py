
from django.urls import path

from . import views

urlpatterns = [
    path("", views.portada, name="home"),
    path("rutinas/", views.lista_rutinas, name="lista_rutinas"),
    path("rutinas/<int:pk>/", views.detalle_rutina, name="detalle_rutina"),
]