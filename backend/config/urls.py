from django.urls import path

from .views import SaudeView

urlpatterns = [
    path("api/saude/", SaudeView.as_view(), name="saude"),
]
