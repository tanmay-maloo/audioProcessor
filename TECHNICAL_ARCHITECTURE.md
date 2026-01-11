# Technical Architecture - Image Generation Integration

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      User/Client                                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Django REST API                            │
├─────────────────────────────────────────────────────────────────┤
│ POST   /api/transcribe                                          │
│ GET    /api/transcribe/<uuid>                                   │
│ GET    /api/image/<uuid>                 (NEW)                  │
│ GET    /api/image-info/<uuid>            (NEW)                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
    ┌─────────┐  ┌──────────────┐  ┌──────────────┐
    │   File  │  │  Transcription  │ Image Service
    │  System │  │    Service    │  │ (NEW)       │
    │         │  │ (Enhanced)    │  │             │
    └─────────┘  └──────────────┘  └──────────────┘
         │                │                 │
         │                ▼                 ▼
         │            ┌──────────────┐   ┌──────────────┐
         │            │  AssemblyAI  │   │   Gemini 2.5 │
         │            │  (External)  │   │  (External)  │
         │            └──────────────┘   └──────────────┘
         │
         ▼
    ┌─────────────────────────────────────┐
    │       SQLite Database (DB)          │
    ├─────────────────────────────────────┤
    │ Transcription Model:                │
    │ - uuid (PK)                         │
    │ - audio_filename                    │
    │ - audio_file_path                   │
    │ - status                            │
    │ - transcribed_text                  │
    │ - error_message                     │
    │ - image_path          (NEW)         │
    │ - image_raw           (NEW)         │
    │ - created_at                        │
    │ - updated_at                        │
    └─────────────────────────────────────┘
```

## Data Flow

### Step 1: Audio Upload & Transcription Request
```
Client Request
    │
    ├─ POST /api/transcribe with audio file
    │
    ▼
views.transcribe_audio()
    │
    ├─ Save audio file to media/audio/
    ├─ Create Transcription record (status='pending')
    ├─ Generate UUID for tracking
    │
    ▼
Start Background Thread: start_transcription_async()
    │
    └─ Returns: UUID to client for tracking
```

### Step 2: Background Transcription Processing
```
Background Thread: transcribe_audio_file()
    │
    ├─ Update status to 'processing'
    ├─ Initialize AssemblyAI SDK
    │
    ▼
AssemblyAI API
    │
    ├─ Transcribe audio file
    ├─ Return transcribed text or error
    │
    ▼
Handle Result
    │
    ├─ If Success:
    │   ├─ Update status to 'completed'
    │   ├─ Save transcribed_text
    │   └─ Call _generate_image_from_transcription()
    │
    └─ If Failed:
        ├─ Update status to 'failed'
        └─ Save error_message
```

### Step 3: Background Image Generation (NEW)
```
_generate_image_from_transcription()
    │
    ├─ Extract transcribed_text from Transcription object
    │
    ▼
image_service.create_and_save_image(text_subject)
    │
    ├─ Initialize Google Generative AI SDK
    ├─ Build image generation prompt with text
    │
    ▼
Gemini 2.5 Flash Image API
    │
    ├─ Generate image (PNG format)
    ├─ Return base64-encoded image data
    │
    ▼
Extract & Decode Image Data
    │
    ├─ Parse base64 from API response
    ├─ Decode and save PNG to media/image/
    │
    ▼
Generate Raw Printer Data
    │
    ├─ Load PNG image
    ├─ Resize: 48 bytes/row × variable height
    ├─ Convert to 1-bit via Floyd-Steinberg dithering
    ├─ Pack to LSB-first bytes
    │
    ▼
Save to Database
    │
    ├─ Update Transcription.image_path
    ├─ Update Transcription.image_raw
    ├─ Save to database
    │
    └─ Logging & Error Handling
```

### Step 4: Retrieve Image
```
Client Request
    │
    ├─ GET /api/image/<uuid>?format=file
    │   or
    └─ GET /api/image/<uuid>?format=raw
         │
         ▼
    views.get_image_by_uuid()
         │
         ├─ Fetch Transcription by UUID
         │
         ├─ If format='file':
         │   ├─ Load PNG from disk
         │   ├─ Return with Content-Type: image/png
         │   └─ Client can display/save image
         │
         └─ If format='raw':
             ├─ Load raw binary from database
             ├─ Return with Content-Type: application/octet-stream
             └─ Client sends to printer
```

## File Structure

```
audioProcessor/
├── api/
│   ├── models.py                 (Updated: image_path, image_raw fields)
│   ├── transcription_service.py  (Updated: image generation callback)
│   ├── image_service.py          (NEW: image generation logic)
│   ├── views.py                  (Updated: new API endpoints)
│   ├── urls.py                   (Updated: new routes)
│   ├── management/
│   │   └── commands/
│   │       └── run_udp_receiver.py
│   └── migrations/
│       ├── 0001_initial.py
│       └── 00XX_add_image_fields.py  (NEW: to be created)
├── media/
│   ├── audio/
│   │   └── audio_YYYY-MM-DD_HH-MM-SS.wav  (audio files)
│   └── image/
│       └── genai_response_YYYYMMDDTHHMMSSZ.png  (generated images)
└── ...other Django files...
```

## Module Responsibilities

### `models.py` - Data Schema
- **Transcription Model**: Stores transcription metadata, text, and image data
- **New Fields**:
  - `image_path`: Path to PNG file on disk
  - `image_raw`: Binary blob for printer (stored in database for quick access)

### `transcription_service.py` - Background Processing
- **`transcribe_audio_file()`**: Handles AssemblyAI transcription
- **`_generate_image_from_transcription()`**: (NEW) Callback after transcription
- **`start_transcription_async()`**: Spawns background thread

### `image_service.py` - Image Generation (NEW)
- **`create_and_save_image()`**: Main image generation function
  - Calls Gemini 2.5 Flash API
  - Saves PNG to disk
  - Generates raw printer data
  - Returns both paths/data
- **`_generate_raw_image_data()`**: Converts PNG to printer-format binary
  - Resizes to 48 bytes per row
  - Floyd-Steinberg dithering
  - LSB-first bit packing

### `views.py` - API Endpoints (Enhanced)
- **`transcribe_audio()`**: (Existing) Upload audio → start transcription
- **`get_image_by_uuid()`**: (NEW) Retrieve image by UUID
  - `?format=file`: PNG image
  - `?format=raw`: Binary data
- **`get_transcription_image_info()`**: (NEW) Get image metadata

### `urls.py` - Route Mapping (Updated)
- `image/<uuid:uuid>`: Image retrieval endpoint
- `image-info/<uuid:uuid>`: Image info endpoint

## Concurrency & Threading

### Background Thread Model
- Each transcription request spawns a daemon thread
- Thread runs `transcribe_audio_file()` → `_generate_image_from_transcription()`
- Image generation happens in same thread after transcription completes
- No blocking on main request handler

### Database Consistency
- Each operation uses Django ORM atomic operations
- No race conditions: UUID is primary key
- Error updates are safe with try/except

## Error Handling Strategy

### Transcription Errors
- Assembly AI API error → Status set to 'failed' → Error message saved

### Image Generation Errors
- Network error → Transcription stays 'completed' → Error logged + message appended
- API error → Transcription stays 'completed' → Error logged + message appended
- File system error → Transcription stays 'completed' → Error logged + message appended
- **Rationale**: Transcription is valuable even without image

### API Endpoint Errors
- UUID not found → 404
- Image not ready → 202 Accepted
- Invalid format → 400 Bad Request
- Server error → 500

## Performance Considerations

### Image Raw Data Storage
- Stored in database BinaryField for quick access
- No need for file system lookup on retrieval
- Typical size: 28-40KB per image (48×variable resolution)

### Image File Storage
- PNG stored on disk at media/image/
- Path stored in database for reference
- Suitable for long-term storage + filesystem operations

### API Response Performance
- `format=raw`: Direct binary stream (~28KB typical)
- `format=file`: Stream PNG from disk or memory
- Headers provide metadata without full response parsing

## Security Considerations

1. **API Key Management**
   - GOOGLE_API_KEY from environment variables only
   - Never logged or exposed in responses

2. **File Uploads**
   - Audio files stored with timestamp + extension validation
   - Saved in MEDIA_ROOT (configurable, outside web root)

3. **Image Generation**
   - No user-controlled prompt injection (text extracted from transcription)
   - Image stored in MEDIA_ROOT

4. **API Access**
   - UUID-based access (not sequential IDs)
   - No enumeration attacks possible
   - CSRF protection maintained

## Scalability & Future Improvements

### Current Limitations
- Transcription + image generation in same thread (sequential)
- Image stored in single media directory

### Scaling Opportunities
1. Separate image generation to independent thread/process
2. Implement job queue (Celery/Redis) for async tasks
3. Store images in cloud storage (S3/GCS)
4. Cache generated images based on text hash
5. Add image regeneration with different parameters
6. Implement rate limiting per UUID/IP
7. Add support for multiple image generation models
8. Implement image batch processing

### Database Considerations
- BinaryField suitable for small-medium images (~1MB)
- For larger deployments: externalize to S3, store URL in DB
- Add indexes on UUID, created_at for faster queries

## Testing Strategy

### Unit Tests
- `test_transcription_service.py`: Mock AssemblyAI API
- `test_image_service.py`: Mock Gemini API
- `test_api_endpoints.py`: Test all 3 endpoints

### Integration Tests
- End-to-end audio → transcription → image → retrieval
- Error scenarios: failed transcription, failed image generation

### Manual Testing
```bash
# 1. Upload audio
curl -X POST http://localhost:8000/api/transcribe -F "audio_file=@test.wav"

# 2. Poll for completion
while true; do
  curl http://localhost:8000/api/image-info/UUID | jq '.'
  sleep 2
done

# 3. Download image
curl -o test_output.png "http://localhost:8000/api/image/UUID?format=file"

# 4. Verify raw data
curl -o test_output.bin "http://localhost:8000/api/image/UUID?format=raw"
```

## Deployment Checklist

- [ ] Create database migration: `python manage.py makemigrations api`
- [ ] Apply migration: `python manage.py migrate`
- [ ] Set `GOOGLE_API_KEY` environment variable
- [ ] Ensure `ASSEMBLYAI_API_KEY` is set
- [ ] Install required packages: `google-generativeai`, `pillow`
- [ ] Verify `media/image/` directory exists and is writable
- [ ] Verify `media/audio/` directory exists and is writable
- [ ] Test image generation in staging environment
- [ ] Monitor logs for image generation errors
- [ ] Set up log rotation for long-running instances
