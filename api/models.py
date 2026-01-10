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

