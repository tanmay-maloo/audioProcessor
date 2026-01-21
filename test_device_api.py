#!/usr/bin/env python3
"""
Test script for the new device-based image API endpoints.
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"
DEVICE_ID = "test_device_001"

def test_device_status():
    """Test the device status endpoint"""
    print(f"Testing device status for {DEVICE_ID}...")
    
    response = requests.get(f"{BASE_URL}/device/{DEVICE_ID}/status")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
    
    return response.json()

def test_transcribe_with_device_id():
    """Test transcription with device_id parameter"""
    print(f"Testing transcription with device_id={DEVICE_ID}...")
    
    # Check if test.wav exists
    try:
        with open('test.wav', 'rb') as f:
            files = {'audio_file': f}
            params = {'device_id': DEVICE_ID}
            
            response = requests.post(f"{BASE_URL}/transcribe", files=files, params=params)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            print()
            
            return response.json()
    except FileNotFoundError:
        print("test.wav not found. Skipping transcription test.")
        return None

def test_device_image_raw():
    """Test getting raw image data for device"""
    print(f"Testing device image raw for {DEVICE_ID}...")
    
    response = requests.get(f"{BASE_URL}/device/{DEVICE_ID}/image-raw")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Content-Length: {response.headers.get('Content-Length')}")
        print(f"X-Device-ID: {response.headers.get('X-Device-ID')}")
        print("Raw image data received successfully")
    else:
        print(f"Response: {response.text}")
    print()

def test_mark_unavailable():
    """Test marking device image as unavailable"""
    print(f"Testing mark unavailable for {DEVICE_ID}...")
    
    response = requests.post(f"{BASE_URL}/device/{DEVICE_ID}/mark-unavailable")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Response: {response.text}")
    print()

def main():
    """Run all tests"""
    print("=" * 60)
    print("Device-Based Image API Test")
    print("=" * 60)
    
    # Test 1: Check initial device status (should be not found or no image)
    test_device_status()
    
    # Test 2: Try to get image raw (should fail initially)
    test_device_image_raw()
    
    # Test 3: Upload audio with device_id (if test.wav exists)
    transcription_result = test_transcribe_with_device_id()
    
    if transcription_result:
        print("Waiting for transcription and image generation to complete...")
        print("You can manually check the status by running:")
        print(f"curl {BASE_URL}/device/{DEVICE_ID}/status")
        print()
        
        # Wait a bit and check status again
        time.sleep(5)
        status = test_device_status()
        
        if status.get('image_available'):
            print("Image is available! Testing image retrieval...")
            test_device_image_raw()
            
            # Test marking as unavailable
            test_mark_unavailable()
            
            # Check status after marking unavailable
            test_device_status()
        else:
            print("Image not yet available. Check again later.")
    
    print("Test completed!")

if __name__ == "__main__":
    main()