# API Usage Guide - Image Generation Feature

## Workflow Summary

### 1. Upload and Transcribe Audio
```bash
curl -X POST http://localhost:8000/api/transcribe \
  -F "audio_file=@/path/to/audio.wav"
```

**Response**:
```json
{
  "status": "success",
  "message": "Audio file uploaded successfully. Transcription in progress.",
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "file_info": {
    "filename": "audio_2026-01-11_10-30-45.wav",
    "original_filename": "audio.wav",
    "size": 123456
  }
}
```

### 2. Check Transcription and Image Generation Status
```bash
curl http://localhost:8000/api/image-info/550e8400-e29b-41d4-a716-446655440000
```

**Response** (while processing):
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "transcribed_text": "a man eating ice cream while riding a bicycle",
  "has_image": false,
  "image_path": null,
  "image_raw_size": 0,
  "created_at": "2026-01-11T10:30:45Z",
  "updated_at": "2026-01-11T10:30:50Z"
}
```

**Response** (after image generation completes):
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "transcribed_text": "a man eating ice cream while riding a bicycle",
  "has_image": true,
  "image_path": "/path/to/media/image/genai_response_20260111T103145Z.png",
  "image_raw_size": 28416,
  "created_at": "2026-01-11T10:30:45Z",
  "updated_at": "2026-01-11T10:31:05Z"
}
```

### 3. Retrieve Generated Image (PNG File)
```bash
curl -o image.png http://localhost:8000/api/image/550e8400-e29b-41d4-a716-446655440000?format=file
```

or default (file format is default):
```bash
curl -o image.png http://localhost:8000/api/image/550e8400-e29b-41d4-a716-446655440000
```

### 4. Retrieve Raw Binary Data for Printer
```bash
curl -o image.bin http://localhost:8000/api/image/550e8400-e29b-41d4-a716-446655440000?format=raw
```

**Raw Data Specifications**:
- 48 bytes per row (384 pixels width)
- Variable height (depends on original aspect ratio)
- 1-bit dithered using Floyd-Steinberg algorithm
- LSB-first bit packing
- Inverted bits for printer

### 5. Get Full Transcription Status (Original Endpoint)
```bash
curl http://localhost:8000/api/transcribe/550e8400-e29b-41d4-a716-446655440000
```

**Response**:
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "filename": "audio_2026-01-11_10-30-45.wav",
  "transcribed_text": "a man eating ice cream while riding a bicycle",
  "created_at": "2026-01-11T10:30:45Z",
  "updated_at": "2026-01-11T10:31:05Z"
}
```

## Complete Example Workflow

```bash
#!/bin/bash

# 1. Upload audio file
RESPONSE=$(curl -s -X POST http://localhost:8000/api/transcribe \
  -F "audio_file=@speech.wav")

UUID=$(echo $RESPONSE | jq -r '.uuid')
echo "Transcription UUID: $UUID"

# 2. Poll for completion (wait up to 2 minutes)
for i in {1..24}; do
  INFO=$(curl -s http://localhost:8000/api/image-info/$UUID)
  HAS_IMAGE=$(echo $INFO | jq -r '.has_image')
  
  if [ "$HAS_IMAGE" = "true" ]; then
    echo "Image generated successfully!"
    break
  fi
  
  echo "Status: $(echo $INFO | jq -r '.status') (attempt $i/24)"
  sleep 5
done

# 3. Download the image
curl -o generated_image.png http://localhost:8000/api/image/$UUID?format=file
echo "PNG image saved to: generated_image.png"

# 4. Download raw data for printer
curl -o printer_data.bin http://localhost:8000/api/image/$UUID?format=raw
echo "Raw printer data saved to: printer_data.bin"
```

## Error Handling

### Image not yet generated (202 Accepted)
```bash
curl -i http://localhost:8000/api/image/550e8400-e29b-41d4-a716-446655440000
```

**Response**:
```
HTTP/1.1 202 Accepted
Content-Type: application/json

{
  "error": "Image not yet generated",
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Image generation may still be in progress or failed"
}
```

### Transcription not found (404 Not Found)
```bash
curl -i http://localhost:8000/api/image/invalid-uuid
```

**Response**:
```
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "error": "Transcription not found"
}
```

### Invalid format parameter (400 Bad Request)
```bash
curl -i http://localhost:8000/api/image/$UUID?format=invalid
```

**Response**:
```
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "Unknown format: invalid",
  "supported_formats": ["file", "raw", "png"]
}
```

## Response Headers

### For PNG/File Format
```
Content-Type: image/png
Content-Length: 45678
X-Image-UUID: 550e8400-e29b-41d4-a716-446655440000
Content-Disposition: inline; filename="genai_response_20260111T103145Z.png"
```

### For Raw Format
```
Content-Type: application/octet-stream
Content-Length: 28416
X-Image-UUID: 550e8400-e29b-41d4-a716-446655440000
Content-Disposition: attachment; filename="image_raw_550e8400-e29b-41d4-a716-446655440000.bin"
```

## Key Points

1. **Asynchronous Processing**: Image generation happens in the background after transcription completes
2. **Graceful Degradation**: If image generation fails, transcription is still marked as completed
3. **Multiple Formats**: Access images as PNG files or raw binary data
4. **Database Storage**: Both image path and raw data are persisted for quick retrieval
5. **Status Tracking**: Use `/image-info/<uuid>` to track image generation progress

## Integration Notes

- The transcription service automatically triggers image generation after transcription completes
- No additional API calls are needed - everything is handled automatically
- Images are generated with a kid-friendly cartoon style by default
- Raw data is optimized for thermal printer output (48 bytes/row, 1-bit dithered)

## Rate Limiting & Best Practices

- Poll `/image-info/<uuid>` every 5 seconds when waiting for image generation
- Don't poll more frequently than 1 second to avoid server overload
- Cache the UUID returned from the transcribe endpoint for later access
- Use `format=raw` only if you need printer data; PNG is suitable for most use cases
