# Improved API Error Handling Guide

## Overview

The API has been significantly improved with better error handling and clear error messages. The image endpoints now only serve existing images and provide helpful error messages when no images are available.

## Key Improvements

### 1. **Smart Image Endpoints**
- `/genai-image` and `/genai-image-raw` automatically find the most recent generated image
- **No automatic generation** - only serves existing images
- Clear error messages when no images are available

### 2. **Better Error Messages**
- JSON error responses instead of generic HTML 404 pages
- Specific error details and helpful suggestions
- Proper HTTP status codes with meaningful messages

### 3. **Image Availability Check**
- Endpoints check for existing images in the system
- Report how many images are available
- Clear guidance on how to generate images

## API Endpoints

### Image Serving Endpoints

#### GET `/genai-image`
Serves a reduced PNG image (optimized for ESP32) from existing generated images.

**Behavior:**
- Finds the most recent `genai_response_*.png` file
- Reduces image size to ~50KB for ESP32 compatibility
- Returns 404 with helpful message if no images exist

**Examples:**
```bash
# Get existing image
curl "http://localhost:8000/genai-image"
```

**Success Response:**
- Status: 200
- Content-Type: `image/png`
- Headers: `X-Original-Image`, `X-Reduced-Size`, `X-Original-Size`

**Error Response (No Images):**
```json
{
  "error": "No image available",
  "message": "No generated images found in the system",
  "suggestion": "Generate an image first using the transcription API or upload one manually",
  "available_images": 0
}
```

#### GET `/genai-image-raw`
Serves raw binary data for thermal printers from existing generated images.

**Query Parameters:**
- `invert=0|1` - Bit inversion (default: 1)
- `wrap=0|1` - Wrap with printer commands (default: 0)
- `energy=hex` - Energy level for printer (default: 0xffff)

**Examples:**
```bash
# Get raw data for existing image
curl "http://localhost:8000/genai-image-raw"

# Get wrapped printer commands
curl "http://localhost:8000/genai-image-raw?wrap=1"

# Get raw data without bit inversion
curl "http://localhost:8000/genai-image-raw?invert=0"
```

**Success Response:**
- Status: 200
- Content-Type: `application/octet-stream`
- Headers: `X-Original-Image`, `X-Image-Width-Bytes`, `X-Image-Height-Pixels`

**Error Response (No Images):**
```json
{
  "error": "No image available",
  "message": "No generated images found in the system",
  "suggestion": "Generate an image first using the transcription API or upload one manually",
  "available_images": 0
}
```

### UUID-Based Endpoints

#### GET `/image/{uuid}`
Get PNG image for a specific transcription.

**Error Responses:**
```json
{
  "error": "Invalid UUID format: Invalid UUID format: invalid-uuid"
}
```

```json
{
  "error": "Transcription not found"
}
```

```json
{
  "error": "Image not yet generated",
  "uuid": "12345678-1234-1234-1234-123456789012",
  "status": "processing",
  "message": "Image generation may still be in progress or failed"
}
```

#### GET `/image-raw/{uuid}`
Get raw binary data for a specific transcription.

#### GET `/image-info/{uuid}`
Get information about a transcription's image.

### Other Endpoints

#### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "Audio processor API is running"
}
```

#### POST `/transcribe`
Upload audio for transcription.

#### GET `/transcribe/{uuid}`
Get transcription status and results.

## Error Handling Examples

### 1. No Images Available
```bash
# When no genai images exist in the system
curl "http://localhost:8000/genai-image"
```

**Response:**
```json
{
  "error": "No image available",
  "message": "No generated images found in the system",
  "suggestion": "Generate an image first using the transcription API or upload one manually",
  "available_images": 0
}
```

### 2. Invalid UUID Format
```bash
curl "http://localhost:8000/image/invalid-uuid"
```

**Response:**
```json
{
  "error": "Invalid UUID format: Invalid UUID format: invalid-uuid"
}
```

### 3. UUID Not Found
```bash
curl "http://localhost:8000/image/12345678-1234-1234-1234-123456789012"
```

**Response:**
```json
{
  "error": "Transcription not found"
}
```

### 4. Image Not Yet Generated for UUID
```bash
curl "http://localhost:8000/image/valid-uuid-but-no-image"
```

**Response:**
```json
{
  "error": "Image not yet generated",
  "uuid": "12345678-1234-1234-1234-123456789012",
  "status": "processing",
  "message": "Image generation may still be in progress or failed"
}
```

## Testing the API

### 1. Test Health Check
```bash
curl "http://localhost:8000/health"
```

### 2. Test Image Serving (Existing Images Only)
```bash
# Try to get existing image
curl "http://localhost:8000/genai-image" -o test_image.png

# Check if image was served or error returned
file test_image.png || echo "No image available"
```

### 3. Test Raw Data (Existing Images Only)
```bash
# Get raw printer data
curl "http://localhost:8000/genai-image-raw" -o test_raw.bin

# Check raw data size
ls -la test_raw.bin || echo "No raw data available"
```

### 4. Test Error Handling
```bash
# Test invalid UUID
curl "http://localhost:8000/image/invalid" | jq

# Test non-existent UUID
curl "http://localhost:8000/image/00000000-0000-0000-0000-000000000000" | jq
```

### 5. Generate Images (Using Transcription API)
```bash
# Upload audio file for transcription and image generation
curl -X POST -F "audio_file=@your_audio.wav" "http://localhost:8000/transcribe"

# Check transcription status (includes image generation)
curl "http://localhost:8000/transcribe/YOUR_UUID"

# Once completed, images will be available via genai-image endpoints
curl "http://localhost:8000/genai-image"
```

## Configuration

### Environment Variables
```bash
# Required for image generation (via transcription API)
GOOGLE_API_KEY=your_api_key_here

# Optional: Custom model (default: gemini-2.5-flash-image)
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image
```

### Django Settings
Make sure your `settings.py` has:
```python
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
```

## Troubleshooting

### Common Issues

1. **404 Errors**: Make sure Django server is running and URLs are correct
2. **No Images Available**: Generate images using the transcription API first
3. **Empty Responses**: Check server logs for detailed error messages
4. **File Not Found**: Use the transcription API to generate new images

### How to Generate Images

Images are generated through the transcription workflow:

1. **Upload Audio**: Use `POST /transcribe` with an audio file
2. **Wait for Processing**: The system will transcribe audio and generate an image
3. **Access Images**: Use `/genai-image` or `/genai-image-raw` endpoints

### Debugging

Enable detailed logging in Django settings:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'api': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
```

## Summary

The improved API now provides:
- ✅ Clear, actionable error messages
- ✅ No automatic API calls to Gemini for image generation
- ✅ Proper HTTP status codes
- ✅ Helpful suggestions for error resolution
- ✅ Image availability reporting
- ✅ Better logging and debugging information

**Key Change**: The `/genai-image` and `/genai-image-raw` endpoints now only serve existing images and provide clear error messages when no images are available. Images must be generated through the transcription API workflow.