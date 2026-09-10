from django import forms
from django.contrib.auth.models import Group, User

from apps.core.forms import style_form_widgets
from apps.core.permissions import ALL_GROUPS


class LoginForm(forms.Form):
    username = forms.CharField(label="Usuário", max_length=150)
    password = forms.CharField(label="Senha", widget=forms.PasswordInput)


class UserForm(forms.ModelForm):
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput,
        required=False,
        help_text="Preencha para definir ou alterar a senha.",
    )
    group = forms.ModelChoiceField(
        label="Grupo",
        queryset=Group.objects.filter(name__in=ALL_GROUPS).order_by("name"),
        required=True,
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]
        labels = {
            "username": "Usuário",
            "first_name": "Nome",
            "last_name": "Sobrenome",
            "email": "E-mail",
            "is_active": "Ativo",
        }

    def __init__(self, *args, **kwargs):
        self.is_create = kwargs.pop("is_create", False)
        super().__init__(*args, **kwargs)
        self.fields["group"].queryset = Group.objects.filter(name__in=ALL_GROUPS).order_by("name")
        style_form_widgets(self)
        self.fields["username"].help_text = ""
        self.fields["is_active"].help_text = "Desmarque para impedir o login, sem apagar o usuário."
        self.order_fields(
            ["username", "password", "first_name", "last_name", "email", "group", "is_active"]
        )
        if self.is_create:
            self.fields["password"].required = True
        if self.instance.pk:
            current = self.instance.groups.filter(name__in=ALL_GROUPS).first()
            if current:
                self.fields["group"].initial = current.pk

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if self.is_create and not password:
            raise forms.ValidationError("Defina uma senha para o novo usuário.")
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
            group = self.cleaned_data["group"]
            user.groups.set([group])
        return user
