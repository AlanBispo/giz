from django.urls import path

from contas.views import CsrfView, LoginView, LogoutView, MeView

from .views import SaudeView

urlpatterns = [
    path("api/saude/", SaudeView.as_view(), name="saude"),
    path("api/csrf/", CsrfView.as_view(), name="csrf"),
    path("api/login/", LoginView.as_view(), name="login"),
    path("api/logout/", LogoutView.as_view(), name="logout"),
    path("api/me/", MeView.as_view(), name="me"),
]
