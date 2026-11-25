from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("pessoas", views.PessoaViewSet, basename="pessoa")
router.register("anos-letivos", views.AnoLetivoViewSet, basename="ano-letivo")
router.register("bimestres", views.BimestreViewSet, basename="bimestre")
router.register("turmas", views.TurmaViewSet, basename="turma")
router.register("disciplinas", views.DisciplinaViewSet, basename="disciplina")
router.register("vinculos", views.VinculoDocenteViewSet, basename="vinculo")
router.register("matriculas", views.MatriculaViewSet, basename="matricula")

urlpatterns = [path("regras/", views.RegrasView.as_view(), name="regras-escola"), *router.urls]
