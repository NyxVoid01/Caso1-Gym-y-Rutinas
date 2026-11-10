
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