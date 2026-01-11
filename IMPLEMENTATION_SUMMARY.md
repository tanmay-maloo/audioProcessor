# Image Generation Integration - Implementation Summary

## Overview
This implementation integrates Google Generative AI image generation into the audio transcription workflow. After transcription is completed, an image is automatically generated based on the transcribed text, and both the image file and raw binary data are stored in the database.

## Changes Made

### 1. **Database Model Changes** (`api/models.py`)
Added two new fields to the `Transcription` model:
- `image_path` (CharField): Full path to the generated PNG image file
- `image_raw` (BinaryField): Raw binary data processed for the printer

### 2. **New Image Service Module** (`api/image_service.py`)
Created a new service for handling image generation:

#### Main Functions:
- `create_and_save_image(text_subject, output_dir)`: 
  - Generates an image using Google Generative AI (Gemini 2.5 Flash)
  - Saves the PNG to disk
  - Converts to raw binary format for printer
  - Returns: `(image_path, image_raw_data)`

- `_generate_raw_image_data(image_path)`:
  - Converts PNG to raw binary suitable for the printer
  - Resizes to 48 bytes per row (384 pixels) while preserving aspect ratio
  - Uses Floyd-Steinberg dithering for 1-bit conversion
  - Returns: bytes of raw image data

### 3. **Updated Transcription Service** (`api/transcription_service.py`)
Enhanced the transcription workflow:

1. After transcription completes successfully, `_generate_image_from_transcription()` is called
2. Image generation happens in the same background thread context
3. On success: image path and raw data are saved to the database
4. On error: error message is saved but transcription status remains 'completed'

### 4. **New API Endpoints** (`api/views.py`)

#### Endpoint 1: Get Image by UUID
**Route**: `GET /api/image/<uuid>`

**Query Parameters**:
- `format`: 'file' (default), 'raw', or 'png'

**Responses**:
- `format=file` or `format=png`: Returns PNG image file
  - Content-Type: `image/png`
  - Headers: `X-Image-UUID`, `Content-Disposition`

- `format=raw`: Returns binary raw data for printer
  - Content-Type: `application/octet-stream`
  - Headers: `X-Image-UUID`, `Content-Disposition`

- `202 Accepted`: Image not yet generated
- `404 Not Found`: Transcription or image not found
- `400 Bad Request`: Invalid format parameter

#### Endpoint 2: Get Image Info by UUID
**Route**: `GET /api/image-info/<uuid>`

**Response** (JSON):
```json
{
  "uuid": "...",
  "status": "completed|processing|failed",
  "transcribed_text": "...",
  "has_image": true/false,
  "image_path": "...",
  "image_raw_size": 12345,
  "created_at": "2026-01-11T...",
  "updated_at": "2026-01-11T...",
  "error_message": "..." (if applicable)
}
```

### 5. **URL Configuration** (`api/urls.py`)
Added routes:
- `image/<uuid:uuid>`: Get image by UUID
- `image-info/<uuid:uuid>`: Get image information by UUID

## Workflow

```
1. User uploads audio file via POST /api/transcribe
   ↓
2. Audio is saved, Transcription record created with status='pending'
   ↓
3. Background thread starts AssemblyAI transcription
   ↓
4. Transcription completes, status='completed', transcribed_text is saved
   ↓
5. Image generation triggered with transcribed_text as subject
   ↓
6. Image generated via Google Generative AI
   ↓
7. Image saved to disk, raw data generated and saved to database
   ↓
8. User can retrieve via:
   - GET /api/image/<uuid>?format=file → PNG image
   - GET /api/image/<uuid>?format=raw → Binary raw data
   - GET /api/image-info/<uuid> → Image metadata
```

## Required Environment Variables
- `GOOGLE_API_KEY`: Google Generative AI API key
- `ASSEMBLYAI_API_KEY`: AssemblyAI API key (already required)

## Image Generation Settings
- **Model**: Gemini 2.5 Flash Image Preview
- **Output Format**: PNG (685px × 913px, 3:4 aspect ratio)
- **Style**: Black line art, cartoon, coloring book style
- **Processor Settings**: 48 bytes per row (384px width), Floyd-Steinberg dithering

## Database Migration
Run migrations to apply model changes:
```bash
python manage.py makemigrations api
python manage.py migrate
```

## Error Handling
- If transcription succeeds but image generation fails, the transcription status remains 'completed' with an error message
- Failed requests return appropriate HTTP status codes with descriptive error messages
- All operations are logged for debugging

## Future Enhancements
- Add caching for generated images
- Support different image styles/templates
- Add image generation progress tracking
- Implement image regeneration with different parameters
