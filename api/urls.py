from django.urls import path
from . import views

urlpatterns = [
    path('transcribe', views.transcribe_audio, name='transcribe'),
    path('health', views.health_check, name='health'),
    path('test', views.test_api, name='test'),
]

