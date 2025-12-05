import json
import logging
import os
from datetime import datetime
from pathlib import Path
import io
from PIL import Image
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import FileResponse, Http404

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_wav_file(request):
    """
    Handle .wav audio file upload and save it with date and time.
    
    Expected multipart/form-data format:
    - audio_file: .wav audio file
    
    Returns:
    - JSON response with file path and details
    """
    try:
        # Extract the audio file
        audio_file = request.FILES.get('audio_file')
        if not audio_file:
            return Response(
                {'error': 'Missing audio_file parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file extension
        if not audio_file.name.lower().endswith('.wav'):
            return Response(
                {'error': 'Only .wav files are allowed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create audio directory if it doesn't exist
        audio_dir = Path(settings.MEDIA_ROOT) / 'audio'
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with current date and time
        # Format: audio_YYYY-MM-DD_HH-MM-SS.wav
        current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"audio_{current_datetime}.wav"
        file_path = audio_dir / filename
        
        # Save the file
        with open(file_path, 'wb+') as destination:
            for chunk in audio_file.chunks():
                destination.write(chunk)
        
        logger.info(f"Audio file saved: {file_path}, size: {audio_file.size} bytes")
        
        # Prepare response
        response_data = {
            'status': 'success',
            'message': 'Audio file uploaded successfully',
            'file_info': {
                'filename': filename,
                'original_filename': audio_file.name,
                'size': audio_file.size,
                'saved_at': current_datetime,
                'path': str(file_path.relative_to(settings.MEDIA_ROOT))
            }
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Error uploading audio file: {str(e)}")
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


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


@api_view(['GET'])
def get_genai_image(request):
    """
    Serve the genai_response_20251109T120523Z.png image.
    
    Returns:
    - PNG image file
    """
    try:
        # Construct the path to the original image
        image_path = Path(settings.MEDIA_ROOT) / 'image' / 'genai_response_20251109T120523Z.png'

        if not image_path.exists():
            logger.error(f"Image not found at: {image_path}")
            raise Http404("Image not found")

        # Open the image and reduce it while preserving aspect ratio.
        # Default target: ~50 KB for the 1-bit PNG output. This keeps the endpoint
        # lightweight for ESP32 clients.
        target_bytes = 50_000

        with Image.open(image_path) as img:
            orig_w, orig_h = img.size

            # Start at original size and progressively scale down by 90% steps until size <= target
            scale = 1.0
            from io import BytesIO
            reduced_buf = BytesIO()
            while True:
                w = max(1, int(orig_w * scale))
                h = max(1, int(orig_h * scale))
                # preserve aspect ratio by scaling both dims equally
                test_img = img.resize((w, h), resample=Image.LANCZOS).convert('L')
                bw = test_img.point(lambda p: 255 if p > 128 else 0, mode='1')
                reduced_buf.seek(0)
                reduced_buf.truncate(0)
                bw.save(reduced_buf, format='PNG', bits=1)
                size = reduced_buf.tell()
                # stop if good or too small to reduce further
                if size <= target_bytes or (w <= 16 or h <= 16):
                    reduced_buf.seek(0)
                    logger.info(f"Serving reduced image: {image_path} (w={w}, h={h}, bytes={size})")
                    return FileResponse(reduced_buf, content_type='image/png')
                # otherwise reduce scale and try again
                scale = scale * 0.9
    
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error serving image: {str(e)}")
        raise Http404("Error serving image")


@api_view(['GET'])
def get_genai_image_raw(request, invert: int | None = None):
    """
    Serve the image as pre-processed raw printer bytes.

    Behavior:
    - Loads the source PNG from media/image/
    - Resizes to a width of 48 bytes per row (48 * 8 = 384 pixels), preserving aspect ratio
    - Converts to 1-bit using Floyd–Steinberg dithering
    - Optionally inverts bits with ?invert=1 (default true for many printers)
    - Returns raw binary: row-major, packed bytes, no headers
    """
    try:
        image_path = Path(settings.MEDIA_ROOT) / 'image' / 'genai_response_20251109T120523Z.png'
        if not image_path.exists():
            logger.error(f"Image not found at: {image_path}")
            raise Http404("Image not found")

        # Bytes per row requested by the printer
        width_bytes = 48
        width_px = width_bytes * 8

        # inversion can be passed either as path param or query param
        if invert is not None:
            invert_flag = bool(invert)
        else:
            invert_param = request.GET.get('invert', '1')
            invert_flag = invert_param.lower() in ('1', 'true', 'yes')

        with Image.open(image_path) as img:
            orig_w, orig_h = img.size
            # preserve aspect ratio: compute new height for width_px
            new_w = width_px
            new_h = max(1, int(orig_h * (new_w / orig_w)))

            # Resize and dither (Floyd–Steinberg)
            gray = img.resize((new_w, new_h), resample=Image.LANCZOS).convert('L')
            bw = gray.convert('1')  # default uses Floyd–Steinberg dither

            # Pack into raw bytes (MSB-first per row)
            raw = bytearray()
            for y in range(new_h):
                byte = 0
                bits = 0
                for x in range(new_w):
                    pixel = bw.getpixel((x, y))
                    # pixel is 0 (black) or 255 (white)
                    bit = 1 if pixel == 0 else 0
                    if invert_flag:
                        bit ^= 1
                    byte = (byte << 1) | bit
                    bits += 1
                    if bits == 8:
                        raw.append(byte & 0xFF)
                        byte = 0
                        bits = 0
                if bits > 0:
                    byte = byte << (8 - bits)
                    raw.append(byte & 0xFF)

            # Ensure row length
            expected_len = new_h * width_bytes
            if len(raw) != expected_len:
                logger.warning(f"Raw length {len(raw)} does not match expected {expected_len}; adjusting")
                # If width_px didn't match multiple of 8 somehow, trim or pad
                if len(raw) > expected_len:
                    raw = raw[:expected_len]
                else:
                    raw.extend(b'\x00' * (expected_len - len(raw)))

            buf = io.BytesIO(bytes(raw))
            buf.seek(0)
            resp = FileResponse(buf, content_type='application/octet-stream')
            resp['Content-Length'] = str(len(raw))
            resp['X-Image-Width-Bytes'] = str(width_bytes)
            resp['X-Image-Height-Pixels'] = str(new_h)
            return resp

    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error generating raw image data: {e}")
        raise Http404("Error generating raw image data")

