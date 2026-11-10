
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Equipamiento, Inscripcion, Rutina


class PropiedadRutinaTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user("ana_t", password="Clave12345!")
        self.bruno = User.objects.create_user("bruno_t", password="Clave12345!")
        self.rutina = Rutina.objects.create(
            titulo="Rutina de prueba", descripcion="d",
            duracion_minutos=30, cupos=10, entrenador=self.ana,
        )

    def test_dueno_puede_abrir_editar(self):
        self.client.login(username="ana_t", password="Clave12345!")
        r = self.client.get(reverse("editar_rutina", args=[self.rutina.pk]))
        self.assertEqual(r.status_code, 200)

    def test_ajeno_no_puede_editar(self):
        self.client.login(username="bruno_t", password="Clave12345!")
        r = self.client.get(reverse("editar_rutina", args=[self.rutina.pk]))
        self.assertEqual(r.status_code, 403)

    def test_ajeno_no_puede_eliminar(self):
        self.client.login(username="bruno_t", password="Clave12345!")
        r = self.client.post(reverse("eliminar_rutina", args=[self.rutina.pk]))
        self.assertEqual(r.status_code, 403)
        self.assertTrue(Rutina.objects.filter(pk=self.rutina.pk).exists())  # sigue existiendo

    def test_sin_sesion_redirige_al_login(self):
        r = self.client.get(reverse("crear_rutina"))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("login"), r.url)

class EquipamientoFormTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user("ana_t", password="Clave12345!")
        self.equipos = [Equipamiento.objects.create(nombre=f"Equipo {i}") for i in range(6)]
        self.client.login(username="ana_t", password="Clave12345!")

    def datos(self, equipos):
        return {
            "titulo": "Rutina con equipos", "descripcion": "d",
            "duracion_minutos": 30, "cupos": 10, "nivel": "basico",
            "disciplina": "", "equipamiento": [e.pk for e in equipos],
        }

    def test_crear_guarda_dueno_y_equipamiento(self):
        self.client.post(reverse("crear_rutina"), self.datos(self.equipos[:2]))
        rutina = Rutina.objects.get(titulo="Rutina con equipos")
        self.assertEqual(rutina.entrenador, self.ana)          # dueño automático
        self.assertEqual(rutina.equipamiento.count(), 2)       # save_m2m funcionó
        self.assertIsNone(rutina.disciplina)                   # catálogo opcional

    def test_mas_de_cinco_equipamientos_no_se_guarda(self):
        r = self.client.post(reverse("crear_rutina"), self.datos(self.equipos))   # 6
        self.assertEqual(r.status_code, 200)                   # vuelve al formulario con error
        self.assertFalse(Rutina.objects.filter(titulo="Rutina con equipos").exists())

class InscripcionTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user("ana_t", password="Clave12345!")
        self.carla = User.objects.create_user("carla_t", password="Clave12345!")
        self.bruno = User.objects.create_user("bruno_t", password="Clave12345!")
        self.rutina = Rutina.objects.create(
            titulo="Rutina de Ana", descripcion="d",
            duracion_minutos=30, cupos=5, entrenador=self.ana,
        )

    def entrar(self, username):
        self.client.login(username=username, password="Clave12345!")

    def test_socio_no_se_inscribe_dos_veces(self):
        self.entrar("carla_t")
        url = reverse("inscribirse", args=[self.rutina.pk])
        self.client.post(url, {"comentario": "hola"})
        self.client.post(url, {"comentario": "otra vez"})
        self.assertEqual(Inscripcion.objects.filter(rutina=self.rutina, socio=self.carla).count(), 1)

    def test_no_puede_inscribirse_en_rutina_propia(self):
        self.entrar("ana_t")
        self.client.post(reverse("inscribirse", args=[self.rutina.pk]), {"comentario": ""})
        self.assertFalse(Inscripcion.objects.filter(rutina=self.rutina, socio=self.ana).exists())

    def test_ajeno_no_puede_cambiar_estado(self):
        i = Inscripcion.objects.create(rutina=self.rutina, socio=self.carla)
        self.entrar("bruno_t")
        r = self.client.post(reverse("cambiar_estado_inscripcion", args=[i.pk]), {"estado": "confirmada"})
        self.assertEqual(r.status_code, 403)
        i.refresh_from_db()
        self.assertEqual(i.estado, "pendiente")

    def test_dueno_confirma_inscripcion(self):
        i = Inscripcion.objects.create(rutina=self.rutina, socio=self.carla)
        self.entrar("ana_t")
        self.client.post(reverse("cambiar_estado_inscripcion", args=[i.pk]), {"estado": "confirmada"})
        i.refresh_from_db()
        self.assertEqual(i.estado, "confirmada")

    def test_socio_cancela_solo_pendientes(self):
        pendiente = Inscripcion.objects.create(rutina=self.rutina, socio=self.carla)
        self.entrar("carla_t")
        self.client.post(reverse("cancelar_inscripcion", args=[pendiente.pk]))
        self.assertFalse(Inscripcion.objects.filter(pk=pendiente.pk).exists())

        confirmada = Inscripcion.objects.create(rutina=self.rutina, socio=self.carla, estado="confirmada")
        self.client.post(reverse("cancelar_inscripcion", args=[confirmada.pk]))
        self.assertTrue(Inscripcion.objects.filter(pk=confirmada.pk).exists())