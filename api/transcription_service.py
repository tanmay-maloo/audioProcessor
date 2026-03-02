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
        
        logger.info(f"⏱️  [TIMING] Starting transcription for UUID: {transaction_uuid}")
        
        # Record transcription start time
        transcription_start_time = timezone.now()
        
        # Update status to processing
        transcription = Transcription.objects.get(uuid=transaction_uuid)
        transcription.status = 'processing'
        transcription.save()
        
        # Configure transcription settings
        config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.slam_1
        )
        
        # Create transcriber and transcribe
        logger.info(f"⏱️  [TIMING] Calling AssemblyAI API for {transaction_uuid}")
        api_call_start = timezone.now()
        
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(audio_file_path)
        
        api_call_end = timezone.now()
        api_call_duration = (api_call_end - api_call_start).total_seconds()
        logger.info(f"⏱️  [TIMING] AssemblyAI API call completed in {api_call_duration:.2f}s")
        
        # Check transcription result
        if transcript.status == aai.TranscriptStatus.error:
            logger.error(f"❌ Transcription failed for {transaction_uuid}: {transcript.error}")
            transcription.status = 'failed'
            transcription.error_message = str(transcript.error)
            transcription.save()
        else:
            # Calculate transcription time
            transcription_end_time = timezone.now()
            transcription_duration = (transcription_end_time - transcription_start_time).total_seconds()
            
            logger.info(f"✅ Transcription completed for {transaction_uuid}")
            logger.info(f"📝 Transcribed text: '{transcript.text}'")
            logger.info(f"⏱️  [TIMING] Total speech-to-text time: {transcription_duration:.2f}s")
            
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
        from .models import DeviceImage
        
        # Record image generation start time
        image_start_time = timezone.now()
        
        logger.info(f"⏱️  [TIMING] Starting image generation for transcription {transcription.uuid}")
        logger.info(f"📝 Transcribed text: '{transcription.transcribed_text}'")
        
        # Generate image with transcribed text as subject
        image_path, image_raw_data = create_and_save_image(transcription.transcribed_text)
        
        # Record image generation end time
        image_end_time = timezone.now()
        
        # Record database save start time
        db_save_start = timezone.now()
        
        # Save image path and raw data to the transcription record
        transcription.image_path = image_path
        transcription.image_raw = image_raw_data
        transcription.save()
        
        db_save_end = timezone.now()
        db_save_duration = (db_save_end - db_save_start).total_seconds()
        
        logger.info(f"⏱️  [TIMING] Database save for transcription {transcription.uuid}: {db_save_duration:.2f}s")
        
        # Update DeviceImage table if device_id is present
        if transcription.device_id:
            device_update_start = timezone.now()
            
            device_image, created = DeviceImage.objects.get_or_create(
                device_id=transcription.device_id,
                defaults={
                    'image_available': True,
                    'image_path': image_path,
                    'image_raw': image_raw_data,
                    'transcript_available': True,
                    'transcript': transcription.transcribed_text
                }
            )
            if not created:
                # Update existing record
                device_image.image_available = True
                device_image.image_path = image_path
                device_image.image_raw = image_raw_data
                device_image.transcript_available = True
                device_image.transcript = transcription.transcribed_text
                device_image.save()
            
            device_update_end = timezone.now()
            device_update_duration = (device_update_end - device_update_start).total_seconds()
            
            logger.info(f"⏱️  [TIMING] DeviceImage update for device_id {transcription.device_id}: {device_update_duration:.2f}s")
        
        # Calculate image generation time
        image_duration = (image_end_time - image_start_time).total_seconds()
        
        logger.info(f"✅ Image generation completed for {transcription.uuid}, saved to {image_path}")
        logger.info(f"⏱️  [TIMING] Text-to-image generation time: {image_duration:.2f}s")
        
        # Log total time from audio upload (created_at) to image saved
        try:
            if transcription.created_at:
                total_elapsed = (image_end_time - transcription.created_at).total_seconds()
                logger.info(f"⏱️  [TIMING] ⭐ TOTAL TIME from audio upload to image stored: {total_elapsed:.2f}s")
                
                # Log breakdown if we have transcription end time
                if transcription_end_time:
                    upload_to_transcription = (transcription_end_time - transcription.created_at).total_seconds()
                    transcription_to_image = (image_end_time - transcription_end_time).total_seconds()
                    logger.info(f"⏱️  [TIMING] Breakdown - Upload→Transcription: {upload_to_transcription:.2f}s, Transcription→Image: {transcription_to_image:.2f}s")
                    logger.info(f"⏱️  [TIMING] Percentage - Transcription: {(upload_to_transcription/total_elapsed)*100:.1f}%, Image: {(transcription_to_image/total_elapsed)*100:.1f}%")
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


