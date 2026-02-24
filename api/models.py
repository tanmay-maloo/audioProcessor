from django.db import models
import uuid


class Transcription(models.Model):
    """
    Model to track audio transcription requests and their status.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this transcription request"
    )
    device_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Device ID from query parameter"
    )
    audio_filename = models.CharField(
        max_length=255,
        help_text="Name of the audio file"
    )
    audio_file_path = models.CharField(
        max_length=512,
        help_text="Full path to the audio file"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the transcription"
    )
    transcribed_text = models.TextField(
        blank=True,
        null=True,
        help_text="The transcribed text result"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if transcription failed"
    )
    image_path = models.CharField(
        max_length=512,
        blank=True,
        null=True,
        help_text="Full path to the generated image file"
    )
    image_raw = models.BinaryField(
        blank=True,
        null=True,
        help_text="Raw binary data for the processed image"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the transcription request was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the transcription was last updated"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Transcription'
        verbose_name_plural = 'Transcriptions'
    
    def __str__(self):
        return f"Transcription {self.uuid} - {self.status}"


class DeviceImage(models.Model):
    """
    Model to track device-specific image availability and data.
    """
    device_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique device identifier"
    )
    image_available = models.BooleanField(
        default=False,
        help_text="Whether an image is available for this device"
    )
    image_path = models.CharField(
        max_length=512,
        blank=True,
        null=True,
        help_text="Full path to the generated image file"
    )
    image_raw = models.BinaryField(
        blank=True,
        null=True,
        help_text="Raw binary data for the processed image"
    )
    transcript_available = models.BooleanField(
        default=False,
        help_text="Whether a transcript is available for this device"
    )
    transcript = models.TextField(
        blank=True,
        null=True,
        help_text="The transcribed text"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the device image record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the device image was last updated"
    )
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Device Image'
        verbose_name_plural = 'Device Images'
    
    def __str__(self):
        return f"Device {self.device_id} - Available: {self.image_available}"

