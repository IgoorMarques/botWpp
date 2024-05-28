from django.urls import path
from .views import WebhookView, SendMessage

urlpatterns = [
    path('webhook/', WebhookView.as_view(), name='webhook'),
    path('mensagem/', SendMessage.as_view(), name='mensagem'),
]
