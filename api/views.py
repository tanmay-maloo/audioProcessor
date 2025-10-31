import json
import logging
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def transcribe_audio(request):
    """
    Handle audio file upload with configuration metadata.
    
    Expected multipart/form-data format:
    - config: JSON string with audio configuration (encoding, sampleRateHz, languageCode, audioChannelCount)
    - audio_file: Raw audio file data
    
    Returns:
    - JSON response with transcribed text
    """
    try:
        # Extract the config JSON from the request
        config_data = request.POST.get('config')
        if not config_data:
            return Response(
                {'error': 'Missing config parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse the config JSON
        try:
            config = json.loads(config_data)
        except json.JSONDecodeError:
            return Response(
                {'error': 'Invalid JSON in config parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract the audio file
        audio_file = request.FILES.get('audio_file')
        if not audio_file:
            return Response(
                {'error': 'Missing audio_file parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Log the received data
        logger.info(f"Received audio file: {audio_file.name}, size: {audio_file.size} bytes")
        logger.info(f"Config: {config}")
        
        # Validate config parameters
        required_fields = ['encoding', 'sampleRateHz', 'languageCode', 'audioChannelCount']
        missing_fields = [field for field in required_fields if field not in config]
        if missing_fields:
            return Response(
                {'error': f'Missing required config fields: {", ".join(missing_fields)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Read the audio data
        audio_data = audio_file.read()
        logger.info(f"Read {len(audio_data)} bytes of audio data")
        
        # Here you would typically:
        # 1. Save the audio file if needed
        # 2. Process the audio (e.g., send to speech-to-text service)
        # 3. Return the transcribed text
        
        # For now, we'll return a mock response
        # In production, you would integrate with a speech-to-text API
        # such as Google Cloud Speech-to-Text, Azure Speech, or AWS Transcribe
        
        # Example of how to save the file (optional):
        # from django.core.files.storage import default_storage
        # file_path = default_storage.save(f'uploads/{audio_file.name}', audio_file)
        
        # Mock transcription response
        transcribed_text = "this is the transcribed text"
        
        return Response(
            {'text': transcribed_text},
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        logger.error(f"Error processing audio upload: {str(e)}")
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def health_check(request):
    """
    Simple health check endpoint to verify the API is running.
    """
    return Response(
        {
            'status': 'healthy',
            'message': 'Audio processor API is running'
        },
        status=status.HTTP_200_OK
    )


@csrf_exempt
@api_view(['GET', 'POST'])
def test_api(request):
    """
    Test API endpoint for debugging and testing ESP32 connections.
    Logs all incoming requests with detailed information.
    """
    # Log the request method and path
    logger.info(f"=" * 80)
    logger.info(f"TEST API HIT!")
    logger.info(f"Method: {request.method}")
    logger.info(f"Path: {request.path}")
    
    # Log headers
    logger.info(f"Headers:")
    for key, value in request.headers.items():
        logger.info(f"  {key}: {value}")
    
    # Log query parameters
    if request.GET:
        logger.info(f"Query Parameters: {dict(request.GET)}")
    
    # Log request body for POST
    if request.method == 'POST':
        # Log content type to help debug
        content_type = request.content_type
        logger.info(f"Content-Type: {content_type}")
        
        # Check for POST data (form data)
        if request.POST:
            logger.info(f"POST Data: {dict(request.POST)}")
        
        # Check for uploaded files
        if request.FILES:
            logger.info(f"Files: {list(request.FILES.keys())}")
            for key, file in request.FILES.items():
                logger.info(f"  {key}: {file.name} ({file.size} bytes)")
        
        # If no POST data or files, try to log raw body
        # Note: body can only be read if POST/FILES haven't been accessed yet
        if not request.POST and not request.FILES:
            try:
                body = request.body
                if body:
                    # Try to decode as UTF-8 for text data
                    try:
                        body_str = body.decode('utf-8')
                        logger.info(f"Raw Body (first 500 chars): {body_str[:500]}")
                    except UnicodeDecodeError:
                        logger.info(f"Raw Body (binary, length): {len(body)} bytes")
                        logger.info(f"Raw Body (hex preview): {body[:100].hex()}")
            except Exception as e:
                logger.info(f"Could not read body: {str(e)}")
    
    # Log client IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    logger.info(f"Client IP: {ip}")
    
    logger.info(f"=" * 80)
    
    # Return success response with request info
    response_data = {
        'status': 'success',
        'message': 'Test API endpoint hit successfully',
        'request_info': {
            'method': request.method,
            'path': request.path,
            'client_ip': ip,
            'content_type': request.content_type,
            'headers': dict(request.headers),
            'query_params': dict(request.GET),
        }
    }
    
    if request.method == 'POST':
        response_data['request_info']['post_data'] = dict(request.POST) if request.POST else {}
        response_data['request_info']['files'] = list(request.FILES.keys()) if request.FILES else []
    
    return Response(response_data, status=status.HTTP_200_OK)

