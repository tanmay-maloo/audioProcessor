# Audio Transcription API Documentation

This document describes the audio transcription API endpoints using AssemblyAI.

## Overview

The transcription system works asynchronously:
1. Upload an audio file to `/api/transcribe`
2. Receive a UUID to track the transcription
3. Poll `/api/transcribe/<uuid>` to check the status and retrieve the result

## API Endpoints

### 1. Upload Audio for Transcription

**Endpoint:** `POST /api/transcribe`

**Content-Type:** `multipart/form-data`

**Request Parameters:**
- `audio_file` (required): The audio file to transcribe (supports .wav, .mp3, .m4a, etc.)

**Example Request (cURL):**
```bash
curl -X POST http://localhost:8000/api/transcribe \
  -F "audio_file=@/path/to/your/audio.wav"
```

**Example Request (Python):**
```python
import requests

url = "http://localhost:8000/api/transcribe"
files = {'audio_file': open('audio.wav', 'rb')}
response = requests.post(url, files=files)
result = response.json()
print(f"UUID: {result['uuid']}")
```

**Success Response (201 Created):**
```json
{
  "status": "success",
  "message": "Audio file uploaded successfully. Transcription in progress.",
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "file_info": {
    "filename": "audio_2025-01-10_14-30-45.wav",
    "original_filename": "audio.wav",
    "size": 1234567,
    "saved_at": "2025-01-10_14-30-45"
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "Missing audio_file parameter"
}
```

---

### 2. Get Transcription Status and Result

**Endpoint:** `GET /api/transcribe/<uuid>`

**URL Parameters:**
- `uuid` (required): The UUID returned from the upload endpoint

**Example Request (cURL):**
```bash
curl http://localhost:8000/api/transcribe/550e8400-e29b-41d4-a716-446655440000
```

**Example Request (Python):**
```python
import requests
import time

url = "http://localhost:8000/api/transcribe/550e8400-e29b-41d4-a716-446655440000"

# Poll until transcription is complete
while True:
    response = requests.get(url)
    result = response.json()
    
    if result['status'] == 'completed':
        print(f"Transcription: {result['transcribed_text']}")
        break
    elif result['status'] == 'failed':
        print(f"Error: {result['error_message']}")
        break
    else:
        print(f"Status: {result['status']}")
        time.sleep(5)  # Wait 5 seconds before checking again
```

**Response - Pending:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "audio_filename": "audio_2025-01-10_14-30-45.wav",
  "created_at": "2025-01-10T14:30:45.123456Z",
  "updated_at": "2025-01-10T14:30:45.123456Z"
}
```

**Response - Processing:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "audio_filename": "audio_2025-01-10_14-30-45.wav",
  "created_at": "2025-01-10T14:30:45.123456Z",
  "updated_at": "2025-01-10T14:30:50.123456Z"
}
```

**Response - Completed:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "audio_filename": "audio_2025-01-10_14-30-45.wav",
  "transcribed_text": "This is the transcribed text from your audio file.",
  "created_at": "2025-01-10T14:30:45.123456Z",
  "updated_at": "2025-01-10T14:31:15.123456Z"
}
```

**Response - Failed:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "audio_filename": "audio_2025-01-10_14-30-45.wav",
  "error_message": "Transcription failed: Invalid audio format",
  "created_at": "2025-01-10T14:30:45.123456Z",
  "updated_at": "2025-01-10T14:31:00.123456Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "error": "Transcription with UUID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

---

## Status Values

| Status | Description |
|--------|-------------|
| `pending` | Transcription request has been received and queued |
| `processing` | AssemblyAI is currently transcribing the audio |
| `completed` | Transcription finished successfully |
| `failed` | Transcription failed (check `error_message` for details) |

---

## Setup Instructions

### 1. Install Dependencies

```bash
cd /Users/tanmaymaloo/Repository/arduino/audioProcessor
source path/to/venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Start the Django Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

---

## Complete Example

Here's a complete Python script that uploads an audio file and waits for the transcription:

```python
import requests
import time

BASE_URL = "http://localhost:8000/api"

def transcribe_audio(audio_file_path):
    """Upload audio file and get transcription."""
    
    # Step 1: Upload audio file
    print("Uploading audio file...")
    with open(audio_file_path, 'rb') as f:
        files = {'audio_file': f}
        response = requests.post(f"{BASE_URL}/transcribe", files=files)
    
    if response.status_code != 201:
        print(f"Error uploading file: {response.text}")
        return None
    
    result = response.json()
    uuid = result['uuid']
    print(f"Upload successful! UUID: {uuid}")
    print(f"File saved as: {result['file_info']['filename']}")
    
    # Step 2: Poll for transcription result
    print("\nWaiting for transcription...")
    while True:
        response = requests.get(f"{BASE_URL}/transcribe/{uuid}")
        
        if response.status_code != 200:
            print(f"Error checking status: {response.text}")
            return None
        
        result = response.json()
        status = result['status']
        print(f"Status: {status}")
        
        if status == 'completed':
            print("\nTranscription completed!")
            print(f"Text: {result['transcribed_text']}")
            return result['transcribed_text']
        elif status == 'failed':
            print(f"\nTranscription failed: {result.get('error_message', 'Unknown error')}")
            return None
        
        # Wait 5 seconds before checking again
        time.sleep(5)

if __name__ == "__main__":
    audio_path = "test.wav"  # Change this to your audio file
    transcription = transcribe_audio(audio_path)
```

---

## Notes

- The API uses the AssemblyAI API with the "best" speech model for high accuracy
- Audio files are saved in the `media/audio/` directory
- The AssemblyAI API key is configured in `api/transcription_service.py`
- Transcription runs in a background thread to avoid blocking the API response
- All transcription requests are stored in the database for tracking and history

---

## Supported Audio Formats

AssemblyAI supports many audio formats including:
- WAV
- MP3
- M4A
- FLAC
- AAC
- OGG
- WebM
- And more...

For best results, use high-quality audio with minimal background noise.

