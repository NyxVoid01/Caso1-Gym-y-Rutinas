
from .models import Disciplina, Rutina
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        label="Correo electrónico",
        required=True,
        help_text="Lo usaremos para identificar tu cuenta. No puede estar repetido.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta registrada con este correo.")
        return email
    
class PerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]   # nunca "password" aquí
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo electrónico",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        # El correo puede ser el mío, pero no el de OTRA persona
        existe = (User.objects
                  .filter(email__iexact=email)
                  .exclude(pk=self.instance.pk)
                  .exists())
        if existe:
            raise forms.ValidationError("Ese correo ya pertenece a otra cuenta.")
        return email

class RutinaForm(forms.ModelForm):
    class Meta:
        model = Rutina

        fields = ["titulo", "descripcion", "duracion_minutos", "cupos", "nivel",
                  "disciplina", "equipamiento"]
        
        labels = {
            "titulo": "Título de la rutina",
            "descripcion": "Descripción",
            "duracion_minutos": "Duración (minutos)",
            "cupos": "Cupos disponibles",
            "nivel": "Nivel",
            "disciplina": "Disciplina",
            "equipamiento": "Equipamiento necesario",
        }

        help_texts = {
            "titulo": "Mínimo 5 caracteres. No puedes repetir el título de otra rutina tuya.",
            "duracion_minutos": "Entre 10 y 120 minutos.",
            "cupos": "Entre 1 y 30 personas.",
            "disciplina": "Opcional: una rutina puede quedar sin disciplina.",
            "equipamiento": "Marca hasta 5.",
        }

        widgets = {
            "descripcion": forms.Textarea(attrs={
                "rows": 4, "placeholder": "Ejercicios, series, descansos..."}),
            "duracion_minutos": forms.NumberInput(attrs={"min": 10, "max": 120}),
            "cupos": forms.NumberInput(attrs={"min": 1, "max": 30}),
            "equipamiento": forms.CheckboxSelectMultiple,   # casillas en vez de lista múltiple
        }

    def __init__(self, *args, entrenador=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.entrenador = entrenador          # lo necesitamos para la validación propia
        self.fields["disciplina"].empty_label = "— Sin disciplina —"

    def clean_titulo(self):
        titulo = " ".join(self.cleaned_data["titulo"].split())   # quita espacios de sobra
        if len(titulo) < 5:
            raise forms.ValidationError("El título debe tener al menos 5 caracteres.")
        if self.entrenador:
            repetido = (Rutina.objects
                        .filter(entrenador=self.entrenador, titulo__iexact=titulo)
                        .exclude(pk=self.instance.pk))           # al editar, no chocar consigo misma
            if repetido.exists():
                raise forms.ValidationError("Ya tienes una rutina con ese título. Usa otro.")
        return titulo

    def clean_equipamiento(self):
        equipos = self.cleaned_data["equipamiento"]
        if len(equipos) > 5:
            raise forms.ValidationError(
                f"Puedes elegir hasta 5 equipamientos (marcaste {len(equipos)})."
            )
        return equipos

class DisciplinaForm(forms.ModelForm):
    class Meta:
        model = Disciplina
        fields = ["nombre"]
        labels = {"nombre": "Nueva disciplina"}
        widgets = {"nombre": forms.TextInput(attrs={"placeholder": "Ej: Pilates"})}

    def clean_nombre(self):
        nombre = " ".join(self.cleaned_data["nombre"].split()).capitalize()
        if len(nombre) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres.")
        if Disciplina.objects.filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError("Esa disciplina ya existe.")
        return nombre