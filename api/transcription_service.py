"""
AssemblyAI Transcription Service
This module handles audio transcription using AssemblyAI API.
"""
import logging
import threading
import os
from pathlib import Path
from dotenv import load_dotenv
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Import assemblyai lazily to handle missing dependency
aai = None

def _init_assemblyai():
    """Initialize AssemblyAI on first use"""
    global aai
    if aai is None:
        try:
            import assemblyai as assemblyai_module
            aai = assemblyai_module
            # Configure AssemblyAI API key from environment variable
            aai.settings.api_key = os.getenv('ASSEMBLYAI_API_KEY')
            if not aai.settings.api_key:
                logger.warning("ASSEMBLYAI_API_KEY environment variable is not set")
        except ImportError as e:
            logger.error(f"Failed to import assemblyai: {e}")
            raise


def transcribe_audio_file(audio_file_path: str, transaction_uuid: str):
    """
    Transcribe an audio file using AssemblyAI.
    This function runs in a background thread.
    
    Args:
        audio_file_path: Full path to the audio file to transcribe
        transaction_uuid: UUID of the transcription request
    """
    from .models import Transcription  # Import here to avoid circular imports
    
    try:
        # Initialize AssemblyAI on first use
        _init_assemblyai()

        # Ensure the API key is set on the SDK settings (double-check)
        try:
            api_key = os.environ.get('ASSEMBLYAI_API_KEY')
            if api_key:
                # set again in case the SDK didn't pick it up earlier
                aai.settings.api_key = api_key
        except Exception:
            logger.exception('Failed to ensure ASSEMBLYAI_API_KEY in assemblyai settings')

        # Log presence (do not log full key)
        try:
            key_present = bool(getattr(aai.settings, 'api_key', None))
            logger.info(f"assemblyai loaded: {aai is not None}, api_key_present: {key_present}")
        except Exception:
            logger.exception('Error checking assemblyai.settings.api_key')
        
        logger.info(f"Starting transcription for UUID: {transaction_uuid}")
        
        # Record transcription start time
        transcription_start_time = timezone.now()
        
        # Update status to processing
        transcription = Transcription.objects.get(uuid=transaction_uuid)
        transcription.status = 'processing'
        transcription.save()
        
        # Configure transcription settings
        config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.best
        )
        
        # Create transcriber and transcribe
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(audio_file_path)
        
        # Check transcription result
        if transcript.status == aai.TranscriptStatus.error:
            logger.error(f"Transcription failed for {transaction_uuid}: {transcript.error}")
            transcription.status = 'failed'
            transcription.error_message = str(transcript.error)
            transcription.save()
        else:
            # Calculate transcription time
            transcription_end_time = timezone.now()
            transcription_duration = (transcription_end_time - transcription_start_time).total_seconds()
            
            logger.info(f"Transcription completed for {transaction_uuid}")
            logger.info(f"Speech-to-text time for {transaction_uuid}: {transcription_duration:.2f}s")
            
            transcription.status = 'completed'
            transcription.transcribed_text = transcript.text
            transcription.save()
            
            # Start image generation with transcribed text as subject
            _generate_image_from_transcription(transcription, transcription_end_time)
            
    except Exception as e:
        logger.error(f"Error during transcription for {transaction_uuid}: {str(e)}")
        try:
            transcription = Transcription.objects.get(uuid=transaction_uuid)
            transcription.status = 'failed'
            transcription.error_message = str(e)
            transcription.save()
        except Exception as save_error:
            logger.error(f"Failed to update transcription status: {str(save_error)}")


def start_transcription_async(audio_file_path: str, transaction_uuid: str):
    """
    Start the transcription process in a background thread.
    
    Args:
        audio_file_path: Full path to the audio file to transcribe
        transaction_uuid: UUID of the transcription request
    """
    thread = threading.Thread(
        target=transcribe_audio_file,
        args=(audio_file_path, transaction_uuid),
        daemon=True
    )
    thread.start()
    logger.info(f"Started background transcription thread for UUID: {transaction_uuid}")


def _generate_image_from_transcription(transcription, transcription_end_time=None):
    """
    Generate an image from the transcribed text and save it.
    This is called after transcription is completed.
    
    Args:
        transcription: Transcription model instance
        transcription_end_time: When transcription completed (for timing logs)
    """
    try:
        from .image_service import create_and_save_image
        
        # Record image generation start time
        image_start_time = timezone.now()
        
        logger.info(f"Starting image generation for transcription {transcription.uuid}")
        
        # Generate image with transcribed text as subject
        image_path, image_raw_data = create_and_save_image(transcription.transcribed_text)
        
        # Record image generation end time
        image_end_time = timezone.now()
        
        # Save image path and raw data to the transcription record
        transcription.image_path = image_path
        transcription.image_raw = image_raw_data
        transcription.save()
        
        # Calculate image generation time
        image_duration = (image_end_time - image_start_time).total_seconds()
        
        logger.info(f"Image generation completed for {transcription.uuid}, saved to {image_path}")
        logger.info(f"Text-to-image time for {transcription.uuid}: {image_duration:.2f}s")
        
        # Log total time from audio upload (created_at) to image saved
        try:
            if transcription.created_at:
                total_elapsed = (image_end_time - transcription.created_at).total_seconds()
                logger.info(f"Total time from audio upload to image stored for {transcription.uuid}: {total_elapsed:.2f}s")
                
                # Log breakdown if we have transcription end time
                if transcription_end_time:
                    upload_to_transcription = (transcription_end_time - transcription.created_at).total_seconds()
                    transcription_to_image = (image_end_time - transcription_end_time).total_seconds()
                    logger.info(f"Time breakdown for {transcription.uuid}: Upload→Transcription: {upload_to_transcription:.2f}s, Transcription→Image: {transcription_to_image:.2f}s")
        except Exception:
            logger.exception("Failed to compute elapsed time for image generation")
        
    except Exception as e:
        logger.error(f"Error during image generation for {transcription.uuid}: {str(e)}")
        # Update error message but keep transcription as completed
        # since the transcription part itself was successful
        try:
            transcription.error_message = f"Transcription completed but image generation failed: {str(e)}"
            transcription.save()
        except Exception as save_error:
            logger.error(f"Failed to update transcription with image generation error: {str(save_error)}")


