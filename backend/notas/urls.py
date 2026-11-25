from django.urls import path

from .views import LancamentoView, NotasView

urlpatterns = [
    path("", NotasView.as_view(), name="nota-list"),
    path("publicacoes/<int:pk>/", LancamentoView.as_view(), name="nota-lancamento"),
]
