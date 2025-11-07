# Audio Processor API

Django REST API for receiving and processing audio files from ESP32 devices.

## Features

- REST API endpoint for uploading audio files via multipart/form-data
- Supports audio configuration metadata (encoding, sample rate, language code, etc.)
- Designed specifically for ESP32 integration
- Returns JSON response with transcribed text

## Installation

### 1. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run migrations

```bash
python manage.py migrate
```

### 4. Create a superuser (optional, for admin access)

```bash
python manage.py createsuperuser
```

### 5. Start the development server

```bash
python manage.py runserver 0.0.0.0:8000
```

The API will be available at `http://localhost:8000/`

## API Endpoints

### POST /upload-wav

Upload a .wav audio file which will be saved with the current date and time.

**Content-Type:** `multipart/form-data`

**Request Body:**

- **audio_file** (file): .wav audio file to upload

**Example using curl:**

```bash
curl -X POST http://localhost:8000/upload-wav \
  -F 'audio_file=@your_audio.wav'
```

**Example using Python:**

```python
import requests

url = 'http://localhost:8000/upload-wav'
files = {'audio_file': open('your_audio.wav', 'rb')}
response = requests.post(url, files=files)
print(response.json())
```

**Response:**

```json
{
  "status": "success",
  "message": "Audio file uploaded successfully",
  "file_info": {
    "filename": "audio_2025-11-07_14-30-45.wav",
    "original_filename": "your_audio.wav",
    "size": 524288,
    "saved_at": "2025-11-07_14-30-45",
    "path": "audio/audio_2025-11-07_14-30-45.wav"
  }
}
```

**Status Codes:**
- 201: Successfully created (file uploaded)
- 400: Bad Request (missing file or invalid file type)
- 500: Internal Server Error

### POST /transcribe

Upload an audio file with configuration metadata for transcription.

**Content-Type:** `multipart/form-data`

**Request Body:**

The request should contain two parts:

1. **config** (form field): JSON string with audio configuration
   ```json
   {
     "encoding": "LINEAR16",
     "sampleRateHz": 16000,
     "languageCode": "en-US",
     "audioChannelCount": 1
   }
   ```

2. **audio_file** (file): Raw audio file data

**Example using curl:**

```bash
curl -X POST http://localhost:8000/transcribe \
  -F 'config={"encoding":"LINEAR16","sampleRateHz":16000,"languageCode":"en-US","audioChannelCount":1}' \
  -F 'audio_file=@recording.raw'
```

**Response:**

```json
{
  "text": "this is the transcribed text"
}
```

**Status Codes:**
- 200: Success
- 400: Bad Request (missing parameters or invalid JSON)
- 500: Internal Server Error

### GET /health

Health check endpoint to verify the API is running.

**Response:**

```json
{
  "status": "healthy",
  "message": "Audio processor API is running"
}
```

## ESP32 Integration

### Arduino/ESP32 Example Code

```cpp
#include <WiFi.h>
#include <HTTPClient.h>

const char* serverUrl = "http://your-server-ip:8000/transcribe";

void uploadAudio(uint8_t* audioData, size_t audioSize) {
    HTTPClient http;
    http.begin(serverUrl);
    
    // Prepare multipart form data
    String boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW";
    String contentType = "multipart/form-data; boundary=" + boundary;
    
    // Build config JSON
    String config = "{\"encoding\":\"LINEAR16\",\"sampleRateHz\":16000,\"languageCode\":\"en-US\",\"audioChannelCount\":1}";
    
    // Build request body
    String requestBody = "";
    requestBody += "--" + boundary + "\r\n";
    requestBody += "Content-Disposition: form-data; name=\"config\"\r\n\r\n";
    requestBody += config + "\r\n";
    requestBody += "--" + boundary + "\r\n";
    requestBody += "Content-Disposition: form-data; name=\"audio_file\"; filename=\"recording.raw\"\r\n";
    requestBody += "Content-Type: application/octet-stream\r\n\r\n";
    
    // Calculate total size
    size_t headerSize = requestBody.length();
    String footer = "\r\n--" + boundary + "--\r\n";
    size_t totalSize = headerSize + audioSize + footer.length();
    
    http.addHeader("Content-Type", contentType);
    http.addHeader("Content-Length", String(totalSize));
    
    // Send request (you'll need to implement streaming for large files)
    WiFiClient* stream = http.getStreamPtr();
    stream->print(requestBody);
    stream->write(audioData, audioSize);
    stream->print(footer);
    
    int httpResponseCode = http.POST("");
    
    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.println("Response: " + response);
    } else {
        Serial.println("Error: " + String(httpResponseCode));
    }
    
    http.end();
}
```

## Configuration

### Settings

Key settings in `audio_processor/settings.py`:

- `DATA_UPLOAD_MAX_MEMORY_SIZE`: Maximum size for uploaded files (default: 50MB)
- `FILE_UPLOAD_MAX_MEMORY_SIZE`: Maximum size for in-memory file uploads (default: 50MB)
- `ALLOWED_HOSTS`: List of allowed hosts (set to `['*']` for development, restrict in production)

### Media Storage

Uploaded files can be saved to the `media/` directory. The API currently returns a mock transcription response. To implement actual transcription:

1. Integrate with a speech-to-text service (e.g., Google Cloud Speech-to-Text, Azure Speech, AWS Transcribe)
2. Update the `transcribe_audio` function in `api/views.py`

## Development

### Running Tests

```bash
python manage.py test
```

### Accessing Admin Panel

1. Create a superuser (see installation step 4)
2. Navigate to `http://localhost:8000/admin/`
3. Log in with your superuser credentials

## Production Deployment

Before deploying to production:

1. Set `DEBUG = False` in settings.py
2. Update `SECRET_KEY` with a secure random key
3. Configure `ALLOWED_HOSTS` with your domain
4. Set up a production database (PostgreSQL, MySQL, etc.)
5. Configure static file serving
6. Use a production WSGI server (gunicorn, uWSGI)
7. Set up HTTPS/SSL certificates
8. Configure CSRF_TRUSTED_ORIGINS if needed

## License

MIT License

## Support

For issues or questions, please open an issue on the repository.

