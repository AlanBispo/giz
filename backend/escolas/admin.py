from django import forms
from django.contrib.admin import AdminSite, ModelAdmin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.http import HttpRequest

from contas.models import Usuario
from contas.selectors import buscar_usuario_por_email
from contas.validators import validar_email_normalizado

from .models import Escola


class EscolaAdminSite(AdminSite):
    site_header = "Administração do Giz"

    def has_permission(self, request: HttpRequest) -> bool:
        return request.user.is_active and request.user.is_superuser


class EscolaAdmin(ModelAdmin):
    fields = ("nome", "media_minima", "pontos_atividades", "pontos_prova")
    readonly_fields = ("media_minima", "pontos_atividades", "pontos_prova")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return super().has_add_permission(request) and not Escola.objects.exists()

    def has_delete_permission(self, request: HttpRequest, obj: Escola | None = None) -> bool:
        return False

    def save_model(
        self, request: HttpRequest, obj: Escola, form: forms.ModelForm, change: bool
    ) -> None:
        if change:
            obj.save(update_fields=["nome"])
        else:
            super().save_model(request, obj, form, change)


class UsuarioCriacaoForm(UserCreationForm):
    email = forms.EmailField(max_length=254, validators=[validar_email_normalizado])

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ("username", "first_name", "last_name", "email", "perfil")

    def clean_email(self) -> str:
        email = self.cleaned_data["email"]
        if buscar_usuario_por_email(email=email) is not None:
            raise ValidationError("Já existe um usuário com este e-mail.")
        return email


class UsuarioAlteracaoForm(UserChangeForm):
    email = forms.EmailField(
        required=False, max_length=254, validators=[validar_email_normalizado]
    )

    class Meta(UserChangeForm.Meta):
        model = Usuario

    def clean_email(self) -> str:
        email = self.cleaned_data["email"]
        usuario = buscar_usuario_por_email(email=email) if email else None
        if usuario and usuario.pk != self.instance.pk:
            raise ValidationError("Já existe um usuário com este e-mail.")
        return email


class UsuarioAdmin(UserAdmin):
    add_form = UsuarioCriacaoForm
    form = UsuarioAlteracaoForm
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username", "first_name", "last_name", "email", "perfil", "password1", "password2"
            ),
        }),
    )
    fieldsets = (*UserAdmin.fieldsets, ("Giz", {"fields": ("perfil",)}))
    readonly_fields = ("perfil", "is_staff", "is_superuser")
    list_display = (*UserAdmin.list_display, "perfil")

    def get_readonly_fields(
        self, request: HttpRequest, obj: Usuario | None = None
    ) -> tuple[str, ...]:
        return self.readonly_fields if obj else ()


site = EscolaAdminSite()
site.register(Escola, EscolaAdmin)
site.register(Usuario, UsuarioAdmin)
