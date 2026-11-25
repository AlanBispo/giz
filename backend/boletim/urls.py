from django.urls import path

from .views import BoletimDaTurmaView, MeuBoletimView

urlpatterns = [
    path("meu/", MeuBoletimView.as_view(), name="meu-boletim"),
    path("turmas/<int:pk>/", BoletimDaTurmaView.as_view(), name="boletim-da-turma"),
]
