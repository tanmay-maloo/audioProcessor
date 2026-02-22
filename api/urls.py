from django.urls import path, re_path
from . import views

urlpatterns = [
    path('upload-wav', views.upload_wav_file, name='upload_wav'),
    path('transcribe', views.transcribe_audio, name='transcribe'),
    # Transcribe endpoint - handles both UUID formats (with/without hyphens)
    re_path(r'^transcribe/([0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12})$', views.get_transcription_status, name='get_transcription_status'),
    # Image endpoints - handle both UUID formats (with/without hyphens)
    re_path(r'^image/([0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12})$', views.get_image_by_uuid, name='get_image_by_uuid'),
    re_path(r'^image-raw/([0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12})$', views.get_image_raw_by_uuid, name='get_image_raw_by_uuid'),
    re_path(r'^image-info/([0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12})$', views.get_transcription_image_info, name='get_transcription_image_info'),
    # Device-based image endpoints
    path('device/<str:device_id>/status', views.get_device_image_status, name='get_device_image_status'),
    path('device/<str:device_id>/image-raw', views.get_device_image_raw, name='get_device_image_raw'),
    path('device/<str:device_id>/mark-unavailable', views.set_device_image_unavailable, name='set_device_image_unavailable'),
    path('device/<str:device_id>/mark-available', views.set_device_image_available, name='set_device_image_available'),
    # General endpoints
    path('health', views.health_check, name='health'),
    path('test', views.test_api, name='test'),
    path('genai-image', views.get_genai_image, name='genai_image'),
    path('genai-image-raw', views.get_genai_image_raw, name='genai_image_raw'),
    path('genai-image-raw/<int:invert>', views.get_genai_image_raw, name='genai_image_raw_invert'),
]