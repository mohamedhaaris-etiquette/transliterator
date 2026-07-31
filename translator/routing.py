from django.urls import path
from .consumers import TranslationConsumer

websocket_urlpatterns = [
    path("ws/translator/", TranslationConsumer.as_asgi()),
]
