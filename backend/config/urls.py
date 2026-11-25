from django.urls import include, path

from contas.views import CsrfView, LoginView, LogoutView, MeView
from escolas.admin import site as admin_escolar

from .views import SaudeView

urlpatterns = [
    path("admin/", admin_escolar.urls),
    path("api/saude/", SaudeView.as_view(), name="saude"),
    path("api/csrf/", CsrfView.as_view(), name="csrf"),
    path("api/login/", LoginView.as_view(), name="login"),
    path("api/logout/", LogoutView.as_view(), name="logout"),
    path("api/me/", MeView.as_view(), name="me"),
    path("api/escola/", include("escolas.urls")),
    path("api/atividades/", include("atividades.urls")),
    path("api/notas/", include("notas.urls")),
]
