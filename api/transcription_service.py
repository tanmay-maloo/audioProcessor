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
        
        logger.info(f"Starting transcription for UUID: {transaction_uuid}")
        
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
            logger.info(f"Transcription completed for {transaction_uuid}")
            transcription.status = 'completed'
            transcription.transcribed_text = transcript.text
            transcription.save()
            
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

