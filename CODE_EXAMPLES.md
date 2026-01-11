# Code Integration Examples

## Frontend Integration Examples

### Example 1: JavaScript/Fetch - Upload and Monitor

```javascript
async function uploadAndTrackImage(audioFile) {
  // Step 1: Upload audio
  const formData = new FormData();
  formData.append('audio_file', audioFile);
  
  const uploadResponse = await fetch('http://localhost:8000/api/transcribe', {
    method: 'POST',
    body: formData
  });
  
  const uploadData = await uploadResponse.json();
  const uuid = uploadData.uuid;
  console.log('Transcription started:', uuid);
  
  // Step 2: Poll for completion
  let imageReady = false;
  let attempts = 0;
  
  while (!imageReady && attempts < 30) {
    const infoResponse = await fetch(`http://localhost:8000/api/image-info/${uuid}`);
    const infoData = await infoResponse.json();
    
    if (infoData.has_image) {
      console.log('Image generated successfully!');
      imageReady = true;
      
      // Step 3: Download image
      const imageResponse = await fetch(`http://localhost:8000/api/image/${uuid}?format=file`);
      const imageBlob = await imageResponse.blob();
      
      // Display or process image
      const imageUrl = URL.createObjectURL(imageBlob);
      document.getElementById('resultImage').src = imageUrl;
      
      return { uuid, imageUrl, imageData: infoData };
    }
    
    console.log(`Status: ${infoData.status} - waiting...`);
    await new Promise(resolve => setTimeout(resolve, 2000));
    attempts++;
  }
  
  if (!imageReady) {
    throw new Error('Image generation timeout');
  }
}

// Usage
const audioInput = document.getElementById('audioFile');
audioInput.addEventListener('change', async (e) => {
  try {
    const result = await uploadAndTrackImage(e.target.files[0]);
    console.log('Success:', result);
  } catch (error) {
    console.error('Error:', error);
  }
});
```

### Example 2: React Component

```jsx
import React, { useState } from 'react';

function ImageGenerationComponent() {
  const [imageUrl, setImageUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [transcribedText, setTranscribedText] = useState(null);

  const handleAudioUpload = async (file) => {
    setLoading(true);
    setError(null);

    try {
      // Upload and get UUID
      const formData = new FormData();
      formData.append('audio_file', file);
      
      const uploadRes = await fetch('/api/transcribe', {
        method: 'POST',
        body: formData
      });
      
      const { uuid } = await uploadRes.json();
      
      // Poll for image
      let imageData = null;
      for (let i = 0; i < 30; i++) {
        const infoRes = await fetch(`/api/image-info/${uuid}`);
        imageData = await infoRes.json();
        
        if (imageData.has_image) break;
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
      
      if (!imageData.has_image) {
        throw new Error('Image generation timeout');
      }
      
      // Set state
      setTranscribedText(imageData.transcribed_text);
      
      // Get image blob
      const imgRes = await fetch(`/api/image/${uuid}?format=file`);
      const blob = await imgRes.blob();
      setImageUrl(URL.createObjectURL(blob));
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Audio to Image Generator</h1>
      
      <input
        type="file"
        accept="audio/*"
        onChange={(e) => e.target.files[0] && handleAudioUpload(e.target.files[0])}
        disabled={loading}
      />
      
      {loading && <p>Processing... This may take a minute.</p>}
      {error && <p style={{color: 'red'}}>Error: {error}</p>}
      
      {transcribedText && (
        <div>
          <h3>Transcribed Text:</h3>
          <p>{transcribedText}</p>
        </div>
      )}
      
      {imageUrl && (
        <div>
          <h3>Generated Image:</h3>
          <img src={imageUrl} alt="Generated" style={{maxWidth: '400px'}} />
        </div>
      )}
    </div>
  );
}

export default ImageGenerationComponent;
```

### Example 3: Vue.js Component

```vue
<template>
  <div class="container">
    <h1>Audio to Image Generator</h1>
    
    <input
      type="file"
      accept="audio/*"
      @change="handleFileSelect"
      :disabled="loading"
    />
    
    <div v-if="loading" class="loading">
      Processing... This may take a minute.
    </div>
    
    <div v-if="error" class="error">
      {{ error }}
    </div>
    
    <div v-if="transcribedText" class="transcription">
      <h3>Transcribed Text:</h3>
      <p>{{ transcribedText }}</p>
    </div>
    
    <div v-if="imageUrl" class="image">
      <h3>Generated Image:</h3>
      <img :src="imageUrl" alt="Generated" />
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      loading: false,
      error: null,
      imageUrl: null,
      transcribedText: null
    };
  },
  methods: {
    async handleFileSelect(event) {
      const file = event.target.files[0];
      if (!file) return;
      
      this.loading = true;
      this.error = null;
      
      try {
        // Upload audio
        const formData = new FormData();
        formData.append('audio_file', file);
        
        const uploadRes = await fetch('/api/transcribe', {
          method: 'POST',
          body: formData
        });
        
        const { uuid } = await uploadRes.json();
        
        // Poll for image
        let imageData = null;
        for (let i = 0; i < 30; i++) {
          const infoRes = await fetch(`/api/image-info/${uuid}`);
          imageData = await infoRes.json();
          
          if (imageData.has_image) break;
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
        if (!imageData.has_image) {
          throw new Error('Image generation timeout');
        }
        
        // Display results
        this.transcribedText = imageData.transcribed_text;
        
        const imgRes = await fetch(`/api/image/${uuid}?format=file`);
        const blob = await imgRes.blob();
        this.imageUrl = URL.createObjectURL(blob);
        
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.container { max-width: 600px; margin: 0 auto; }
.loading { color: blue; }
.error { color: red; }
.transcription { margin: 20px 0; }
.image img { max-width: 100%; }
</style>
```

## Backend Integration Examples

### Example 1: Django View Integration

```python
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.models import Transcription
import requests

@api_view(['POST'])
def bulk_transcribe_and_generate(request):
    """
    Bulk upload multiple audio files and generate images
    """
    audio_files = request.FILES.getlist('audio_files')
    
    if not audio_files:
        return Response(
            {'error': 'No audio files provided'},
            status=400
        )
    
    results = []
    for audio_file in audio_files:
        # Create a mock POST request for each file
        from rest_framework.request import Request
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        mock_request = factory.post('/api/transcribe')
        mock_request.FILES['audio_file'] = audio_file
        
        # Use the standard transcribe endpoint
        from api.views import transcribe_audio
        response = transcribe_audio(mock_request)
        
        if response.status_code == 201:
            results.append(response.data)
    
    return Response({
        'status': 'success',
        'total': len(audio_files),
        'processed': len(results),
        'uuids': [r['uuid'] for r in results]
    })

@api_view(['GET'])
def batch_image_status(request):
    """
    Check status of multiple transcription/image generation requests
    """
    uuids = request.GET.getlist('uuids')
    
    statuses = []
    for uuid in uuids:
        try:
            transcription = Transcription.objects.get(uuid=uuid)
            statuses.append({
                'uuid': str(uuid),
                'status': transcription.status,
                'has_image': bool(transcription.image_path and transcription.image_raw),
                'transcribed_text': transcription.transcribed_text
            })
        except Transcription.DoesNotExist:
            statuses.append({
                'uuid': uuid,
                'error': 'Not found'
            })
    
    return Response(statuses)
```

### Example 2: Command Line Integration

```python
# management/commands/bulk_process_audio.py

from django.core.management.base import BaseCommand
from pathlib import Path
from django.conf import settings
from api.transcription_service import start_transcription_async
from api.models import Transcription

class Command(BaseCommand):
    help = 'Bulk process audio files in a directory'
    
    def add_arguments(self, parser):
        parser.add_argument('directory', type=str)
        parser.add_argument('--extension', default='wav')
    
    def handle(self, *args, **options):
        directory = Path(options['directory'])
        extension = options['extension']
        
        audio_files = directory.glob(f'*.{extension}')
        
        for audio_file in audio_files:
            self.stdout.write(f'Processing: {audio_file.name}')
            
            # Create transcription record
            transcription = Transcription.objects.create(
                audio_filename=audio_file.name,
                audio_file_path=str(audio_file),
                status='pending'
            )
            
            # Start background transcription
            start_transcription_async(str(audio_file), str(transcription.uuid))
            
            self.stdout.write(self.style.SUCCESS(f'✓ UUID: {transcription.uuid}'))
```

### Example 3: Signal Handlers for Custom Processing

```python
# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from api.models import Transcription
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Transcription)
def on_image_generated(sender, instance, created, **kwargs):
    """
    Custom signal handler when image is generated
    """
    if instance.image_path and instance.image_raw and not created:
        # Image just completed
        logger.info(f'Image generated for {instance.uuid}')
        
        # You could:
        # 1. Send email notification
        # 2. Post to webhook
        # 3. Update external system
        # 4. Trigger further processing
        
        send_notification_webhook({
            'uuid': str(instance.uuid),
            'event': 'image_generated',
            'transcribed_text': instance.transcribed_text,
            'image_size': len(instance.image_raw) if instance.image_raw else 0
        })

def send_notification_webhook(data):
    """Send notification to external service"""
    import requests
    try:
        requests.post('https://your-service.com/webhook', json=data, timeout=5)
    except Exception as e:
        logger.error(f'Webhook error: {e}')

# apps.py
from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    
    def ready(self):
        import api.signals
```

## Testing Examples

### Example 1: Unit Tests

```python
# tests/test_image_service.py
import pytest
from unittest.mock import patch, MagicMock
from api.image_service import create_and_save_image
from pathlib import Path

@patch('api.image_service.genai.GenerativeModel')
def test_create_image_success(mock_genai, tmp_path):
    """Test successful image generation"""
    
    # Mock the API response
    mock_response = MagicMock()
    mock_response.to_dict.return_value = {
        'candidates': [{
            'content': {
                'parts': [{
                    'text': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
                }]
            }
        }]
    }
    
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response
    mock_genai.return_value = mock_model
    
    # Test image generation
    with patch('api.image_service.settings.MEDIA_ROOT', str(tmp_path)):
        image_path, image_raw = create_and_save_image("test subject")
    
    assert image_path is not None
    assert image_raw is not None
    assert Path(image_path).exists()

@patch('api.image_service.Image.open')
def test_generate_raw_image_data(mock_image_open, tmp_path):
    """Test raw image data generation"""
    
    # Mock PIL Image
    mock_img = MagicMock()
    mock_img.size = (685, 913)
    mock_img_opened = MagicMock()
    mock_img_opened.__enter__.return_value = mock_img
    mock_img_opened.__exit__.return_value = False
    mock_image_open.return_value = mock_img_opened
    
    # Mock image operations
    mock_resized = MagicMock()
    mock_gray = MagicMock()
    mock_bw = MagicMock()
    
    mock_img.resize.return_value = mock_resized
    mock_resized.convert.return_value = mock_gray
    mock_gray.convert.return_value = mock_bw
    
    # Mock pixel operations
    mock_bw.getpixel.return_value = 0
    
    from api.image_service import _generate_raw_image_data
    raw_data = _generate_raw_image_data(str(tmp_path / 'test.png'))
    
    assert isinstance(raw_data, bytes)
    assert len(raw_data) > 0
```

### Example 2: Integration Tests

```python
# tests/test_api_integration.py
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from api.models import Transcription
import time

class ImageGenerationIntegrationTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        
        # Create a minimal WAV file
        self.audio_file = SimpleUploadedFile(
            "test.wav",
            b"RIFF" + b"x" * 100,
            content_type="audio/wav"
        )
    
    def test_full_workflow(self):
        """Test complete audio -> transcription -> image workflow"""
        
        # 1. Upload audio
        response = self.client.post(
            '/api/transcribe',
            {'audio_file': self.audio_file},
            content_type='multipart/form-data'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        uuid = data['uuid']
        
        # 2. Check initial status
        status_response = self.client.get(f'/api/image-info/{uuid}')
        status_data = status_response.json()
        self.assertEqual(status_data['status'], 'pending')
        
        # 3. Wait for transcription (skip if testing without real API)
        # time.sleep(15)
        
        # 4. Verify image info endpoint
        info_response = self.client.get(f'/api/image-info/{uuid}')
        self.assertEqual(info_response.status_code, 200)
```

---

## Common Integration Patterns

### Pattern 1: Webhook Notification

```python
import requests
from api.models import Transcription

def notify_webhook_on_completion(transcription_uuid):
    """
    Poll for completion and notify external service via webhook
    """
    webhook_url = "https://your-service.com/notify"
    
    # Poll until ready (with timeout)
    max_attempts = 60  # 5 minutes with 5-second intervals
    for attempt in range(max_attempts):
        transcription = Transcription.objects.get(uuid=transcription_uuid)
        
        if transcription.image_path and transcription.image_raw:
            # Image is ready - notify webhook
            payload = {
                'uuid': str(transcription_uuid),
                'status': 'complete',
                'transcribed_text': transcription.transcribed_text,
                'image_path': transcription.image_path,
                'image_size': len(transcription.image_raw)
            }
            requests.post(webhook_url, json=payload)
            return
        
        if transcription.status == 'failed':
            # Failed - notify webhook
            payload = {
                'uuid': str(transcription_uuid),
                'status': 'failed',
                'error': transcription.error_message
            }
            requests.post(webhook_url, json=payload)
            return
        
        time.sleep(5)
```

### Pattern 2: Batch Processing

```python
def process_audio_directory(directory_path):
    """
    Process all audio files in a directory
    """
    from pathlib import Path
    
    directory = Path(directory_path)
    uuids = []
    
    for audio_file in directory.glob('*.wav'):
        # Upload each file
        with open(audio_file, 'rb') as f:
            response = requests.post(
                'http://localhost:8000/api/transcribe',
                files={'audio_file': f}
            )
        
        if response.status_code == 201:
            uuids.append(response.json()['uuid'])
    
    return uuids
```

---

These examples cover common integration scenarios and can be adapted for your specific use case.
