
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from rutinas.models import Disciplina, Equipamiento, Rutina, Inscripcion


class Command(BaseCommand):
    help = "Carga los datos de prueba mínimos del caso (se puede ejecutar varias veces)."

    @transaction.atomic
    def handle(self, *args, **options):
        # 1) Usuarios (3)
        usuarios = {}
        for username, nombre, email in [
            ("ana", "Ana", "ana@gimnasio.cl"),
            ("bruno", "Bruno", "bruno@gimnasio.cl"),
            ("carla", "Carla", "carla@gimnasio.cl"),
        ]:
            user, creado = User.objects.get_or_create(
                username=username, defaults={"first_name": nombre, "email": email}
            )
            if creado:
                user.set_password("Gym12345!")   # se guarda como hash, nunca en texto
                user.save()
            usuarios[username] = user

        # 2) Catálogo (4) y etiquetas (6)
        disciplinas = {
            n: Disciplina.objects.get_or_create(nombre=n)[0]
            for n in ["Funcional", "Yoga", "Spinning", "Fuerza"]
        }
        equipos = {
            n: Equipamiento.objects.get_or_create(nombre=n)[0]
            for n in ["Mancuernas", "Banco", "Colchoneta", "Barra", "Kettlebell", "Bicicleta"]
        }

        # 3) Rutinas (10): título, entrenador, disciplina, nivel, minutos, cupos, equipamiento
        datos = [
            ("Funcional para principiantes", "ana", "Funcional", "basico", 45, 15, ["Mancuernas", "Colchoneta"]),
            ("HIIT intermedio", "ana", "Funcional", "intermedio", 30, 12, ["Kettlebell", "Colchoneta"]),
            ("Yoga matinal", "ana", "Yoga", "basico", 60, 20, ["Colchoneta"]),
            ("Yoga flow avanzado", "ana", "Yoga", "avanzado", 75, 10, ["Colchoneta"]),
            ("Movilidad y estiramiento", "ana", None, "basico", 20, 25, ["Colchoneta"]),
            ("Spinning de resistencia", "bruno", "Spinning", "intermedio", 50, 18, ["Bicicleta"]),
            ("Spinning por intervalos", "bruno", "Spinning", "avanzado", 40, 18, ["Bicicleta"]),
            ("Fuerza tren superior", "bruno", "Fuerza", "intermedio", 60, 8, ["Mancuernas", "Banco", "Barra"]),
            ("Fuerza tren inferior", "bruno", "Fuerza", "avanzado", 70, 8, ["Barra", "Kettlebell", "Banco"]),
            ("Circuito full body", "bruno", "Funcional", "basico", 35, 30,
             ["Mancuernas", "Kettlebell", "Colchoneta", "Banco", "Barra"]),
        ]
        rutinas = []
        for titulo, entrenador, disc, nivel, minutos, cupos, eq in datos:
            rutina, _ = Rutina.objects.get_or_create(
                titulo=titulo,
                entrenador=usuarios[entrenador],
                defaults={
                    "descripcion": f"Rutina de {titulo.lower()} preparada por {entrenador.title()}.",
                    "disciplina": disciplinas[disc] if disc else None,
                    "nivel": nivel,
                    "duracion_minutos": minutos,
                    "cupos": cupos,
                },
            )
            rutina.equipamiento.set([equipos[e] for e in eq])
            rutinas.append(rutina)

        # 4) Inscripciones (5) en distintos estados; nadie se inscribe en lo propio
        for socio, idx, estado in [
            ("carla", 0, "pendiente"),
            ("carla", 5, "confirmada"),
            ("carla", 7, "rechazada"),
            ("bruno", 2, "pendiente"),
            ("ana", 9, "confirmada"),
        ]:
            Inscripcion.objects.get_or_create(
                rutina=rutinas[idx],
                socio=usuarios[socio],
                defaults={"estado": estado, "comentario": "Me interesa esta rutina."},
            )

        self.stdout.write(self.style.SUCCESS(
            f"Listo: {User.objects.count()} usuarios, {Rutina.objects.count()} rutinas, "
            f"{Disciplina.objects.count()} disciplinas, {Equipamiento.objects.count()} equipamientos, "
            f"{Inscripcion.objects.count()} inscripciones."
        ))