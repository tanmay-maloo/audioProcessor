from django.urls import path
from . import views

urlpatterns = [
    path('upload-wav', views.upload_wav_file, name='upload_wav'),
    path('transcribe', views.transcribe_audio, name='transcribe'),
    path('transcribe/<uuid:uuid>', views.get_transcription_status, name='get_transcription_status'),
    # Canonical endpoints (accept with and without trailing slash)
    path('image/<uuid:uuid>', views.get_image_by_uuid, name='get_image_by_uuid'),
    path('image/<uuid:uuid>/', views.get_image_by_uuid, name='get_image_by_uuid_slash'),
    path('image-info/<uuid:uuid>', views.get_transcription_image_info, name='get_transcription_image_info'),
    path('image-info/<uuid:uuid>/', views.get_transcription_image_info, name='get_transcription_image_info_slash'),
    path('health', views.health_check, name='health'),
    path('test', views.test_api, name='test'),
    path('genai-image', views.get_genai_image, name='genai_image'),
    path('genai-image-raw', views.get_genai_image_raw, name='genai_image_raw'),
    path('genai-image-raw/<int:invert>/', views.get_genai_image_raw, name='genai_image_raw_invert'),
]

