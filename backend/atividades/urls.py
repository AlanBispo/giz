from django.urls import path

from .views import ContextoView, PublicacaoDetalheView, PublicacoesView, SaldoView

urlpatterns = [
    path("contexto/", ContextoView.as_view(), name="contexto-atividades"),
    path("saldo/", SaldoView.as_view(), name="saldo-atividades"),
    path("", PublicacoesView.as_view(), name="publicacao-list"),
    path("<int:pk>/", PublicacaoDetalheView.as_view(), name="publicacao-detail"),
]
