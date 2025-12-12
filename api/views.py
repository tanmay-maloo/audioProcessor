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


# --- Printer wrapping utilities -------------------------------------------------
PRINT_WIDTH = 384


def to_unsigned_byte(val):
    return val if val >= 0 else val & 0xff


def bs(lst):
    return bytearray(map(to_unsigned_byte, lst))


CMD_GET_DEV_STATE = bs([
    81, 120, -93, 0, 1, 0, 0, 0, -1
])

CMD_SET_QUALITY_200_DPI = bs([81, 120, -92, 0, 1, 0, 50, -98, -1])

CMD_GET_DEV_INFO = bs([81, 120, -88, 0, 1, 0, 0, 0, -1])

CMD_LATTICE_START = bs([81, 120, -90, 0, 11, 0, -86, 85, 23,
                        56, 68, 95, 95, 95, 68, 56, 44, -95, -1])

CMD_LATTICE_END = bs([81, 120, -90, 0, 11, 0, -86, 85,
                     23, 0, 0, 0, 0, 0, 0, 0, 23, 17, -1])

CMD_SET_PAPER = bs([81, 120, -95, 0, 2, 0, 48, 0, -7, -1])

CMD_PRINT_IMG = bs([81, 120, -66, 0, 1, 0, 0, 0, -1])

CMD_PRINT_TEXT = bs([81, 120, -66, 0, 1, 0, 1, 7, -1])

CHECKSUM_TABLE = bs([
    0, 7, 14, 9, 28, 27, 18, 21, 56, 63, 54, 49, 36, 35, 42, 45, 112, 119, 126, 121,
    108, 107, 98, 101, 72, 79, 70, 65, 84, 83, 90, 93, -32, -25, -18, -23, -4, -5,
    -14, -11, -40, -33, -42, -47, -60, -61, -54, -51, -112, -105, -98, -103, -116,
    -117, -126, -123, -88, -81, -90, -95, -76, -77, -70, -67, -57, -64, -55, -50,
    -37, -36, -43, -46, -1, -8, -15, -10, -29, -28, -19, -22, -73, -80, -71, -66,
    -85, -84, -91, -94, -113, -120, -127, -122, -109, -108, -99, -102, 39, 32, 41,
    46, 59, 60, 53, 50, 31, 24, 17, 22, 3, 4, 13, 10, 87, 80, 89, 94, 75, 76, 69, 66,
    111, 104, 97, 102, 115, 116, 125, 122, -119, -114, -121, -128, -107, -110, -101,
    -100, -79, -74, -65, -72, -83, -86, -93, -92, -7, -2, -9, -16, -27, -30, -21, -20,
    -63, -58, -49, -56, -35, -38, -45, -44, 105, 110, 103, 96, 117, 114, 123, 124, 81,
    86, 95, 88, 77, 74, 67, 68, 25, 30, 23, 16, 5, 2, 11, 12, 33, 38, 47, 40, 61, 58,
    51, 52, 78, 73, 64, 71, 82, 85, 92, 91, 118, 113, 120, 127, 106, 109, 100, 99, 62,
    57, 48, 55, 34, 37, 44, 43, 6, 1, 8, 15, 26, 29, 20, 19, -82, -87, -96, -89, -78,
    -75, -68, -69, -106, -111, -104, -97, -118, -115, -124, -125, -34, -39, -48, -41,
    -62, -59, -52, -53, -26, -31, -24, -17, -6, -3, -12, -13,
])


def chk_sum(b_arr, i, i2):
    b2 = 0
    for i3 in range(i, i + i2):
        b2 = CHECKSUM_TABLE[(b2 ^ b_arr[i3]) & 0xff]
    return b2


def cmd_feed_paper(how_much):
    b_arr = bs([
        81,
        120,
        -67,
        0,
        1,
        0,
        how_much & 0xff,
        0,
        0xff,
    ])
    b_arr[7] = chk_sum(b_arr, 6, 1)
    return bs(b_arr)


def cmd_set_energy(val):
    b_arr = bs([
        81,
        120,
        -81,
        0,
        2,
        0,
        (val >> 8) & 0xff,
        val & 0xff,
        0,
        0xff,
    ])
    b_arr[8] = chk_sum(b_arr, 6, 2)
    return bs(b_arr)


def cmd_apply_energy():
    b_arr = bs(
        [
            81,
            120,
            -66,
            0,
            1,
            0,
            1,
            0,
            0xff,
        ]
    )
    b_arr[7] = chk_sum(b_arr, 6, 1)
    return bs(b_arr)


def encode_run_length_repetition(n, val):
    res = []
    while n > 0x7f:
        res.append(0x7f | (val << 7))
        n -= 0x7f
    if n > 0:
        res.append((val << 7) | n)
    return res


def run_length_encode(img_row):
    res = []
    count = 0
    last_val = -1
    for val in img_row:
        if val == last_val:
            count += 1
        else:
            res.extend(encode_run_length_repetition(count, last_val))
            count = 1
        last_val = val
    if count > 0:
        res.extend(encode_run_length_repetition(count, last_val))
    return res


def byte_encode(img_row):
    def bit_encode(chunk_start, bit_index):
        return 1 << bit_index if img_row[chunk_start + bit_index] else 0

    res = []
    for chunk_start in range(0, len(img_row), 8):
        byte = 0
        for bit_index in range(8):
            byte |= bit_encode(chunk_start, bit_index)
        res.append(byte)
    return res


def cmd_print_row(img_row):
    encoded_img = run_length_encode(img_row)

    if len(encoded_img) > PRINT_WIDTH // 8:
        encoded_img = byte_encode(img_row)
        b_arr = bs([
            81,
            120,
            -94,
            0,
            len(encoded_img),
            0] + encoded_img + [0, 0xff])
        b_arr[-2] = chk_sum(b_arr, 6, len(encoded_img))
        return b_arr

    b_arr = bs([
        81,
        120,
        -65,
        0,
        len(encoded_img),
        0] + encoded_img + [0, 0xff])
    b_arr[-2] = chk_sum(b_arr, 6, len(encoded_img))
    return b_arr


def cmds_print_img(img, energy: int = 0xffff):
    data = \
        CMD_GET_DEV_STATE + \
        CMD_SET_QUALITY_200_DPI + \
        cmd_set_energy(energy) + \
        cmd_apply_energy() + \
        CMD_LATTICE_START
    for row in img:
        data += cmd_print_row(row)
    data += \
        cmd_feed_paper(25) + \
        CMD_SET_PAPER + \
        CMD_SET_PAPER + \
        CMD_SET_PAPER + \
        CMD_LATTICE_END + \
        CMD_GET_DEV_STATE
    return data


def wrap_raw_bytes_with_print_commands(raw_data, energy: int = 0xffff):
    """Wraps pre-encoded raw image bytes directly into printer commands."""
    logger.info('⏳ Wrapping pre-encoded image bytes with printer commands...')

    bytes_per_row = PRINT_WIDTH // 8
    num_rows = len(raw_data) // bytes_per_row

    if len(raw_data) % bytes_per_row != 0:
        logger.warning(f'⚠️  Data length {len(raw_data)} is not a multiple of {bytes_per_row}')

    data = \
        CMD_GET_DEV_STATE + \
        CMD_SET_QUALITY_200_DPI + \
        cmd_set_energy(energy) + \
        cmd_apply_energy() + \
        CMD_LATTICE_START

    for row_idx in range(num_rows):
        start = row_idx * bytes_per_row
        end = start + bytes_per_row
        row_bytes = list(raw_data[start:end])

        b_arr = bs([
            81,
            120,
            -94,
            0,
            bytes_per_row,
            0] + row_bytes + [0, 0xff])
        b_arr[-2] = chk_sum(b_arr, 6, bytes_per_row)
        data += b_arr

    data += \
        cmd_feed_paper(25) + \
        CMD_SET_PAPER + \
        CMD_SET_PAPER + \
        CMD_SET_PAPER + \
        CMD_LATTICE_END + \
        CMD_GET_DEV_STATE

    logger.info(f'✅ Wrapped {num_rows} rows into {len(data)} bytes of printer commands')
    return data

# -----------------------------------------------------------------------------


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

            # Pack into raw bytes (LSB-first per row)
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
                    # LSB-first: place bit at current bit position (0..7)
                    byte |= (bit << bits)
                    bits += 1
                    if bits == 8:
                        raw.append(byte & 0xFF)
                        byte = 0
                        bits = 0
                if bits > 0:
                    # leftover bits are already in low-order positions; pad high bits with 0
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

            # Optionally wrap the raw bytes into the printer command stream
            wrap_param = request.GET.get('wrap', '0')
            wrap_flag = wrap_param.lower() in ('1', 'true', 'yes')
            if wrap_flag:
                energy_param = request.GET.get('energy')
                try:
                    energy = int(energy_param, 0) if energy_param is not None else 0xffff
                except Exception:
                    energy = 0xffff
                wrapped = wrap_raw_bytes_with_print_commands(bytes(raw), energy=energy)
                buf = io.BytesIO(bytes(wrapped))
                buf.seek(0)
                resp = FileResponse(buf, content_type='application/octet-stream')
                resp['Content-Length'] = str(len(wrapped))
                resp['X-Printer-Wrapped'] = '1'
                resp['X-Image-Width-Bytes'] = str(width_bytes)
                resp['X-Image-Height-Pixels'] = str(new_h)
                return resp

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

