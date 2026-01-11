"""
Image Generation Service using Google Generative AI
This module handles image generation based on transcribed text.
"""
import logging
import os
import re
import base64
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Import genai lazily to handle missing dependency
genai = None

def _init_genai():
    """Initialize Google Generative AI on first use"""
    global genai
    if genai is None:
        try:
            import google.generativeai as genai_module
            genai = genai_module
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                logger.warning("GOOGLE_API_KEY environment variable is not set")
            else:
                genai.configure(api_key=api_key)
        except ImportError as e:
            logger.error(f"Failed to import google.generativeai: {e}")
            raise


def create_and_save_image(text_subject: str, output_dir: str = None) -> tuple:
    """
    Generate an image from text using Google Generative AI and save it locally.
    Also returns the raw image data for the printer.
    
    Args:
        text_subject: The subject/description for the image
        output_dir: Directory to save the image (defaults to media/image/)
    
    Returns:
        tuple: (image_path, image_raw_data) where:
            - image_path: Full path to the saved PNG image
            - image_raw_data: Binary data of the processed image for printer
    """
    from django.conf import settings
    from PIL import Image
    import io
    
    try:
        # Initialize Google Generative AI on first use
        _init_genai()
        
        logger.info(f"Starting image generation for subject: {text_subject}")
        
        # Prepare the image generation prompt
        image_generation_prompt = (
            f"A cheerful, kid-friendly cartoon-style **pure black line art drawing** of a {text_subject}. "
            "**Subject is large and fills the canvas well**, with an expressive face, varied hairstyles, and dynamic pose. "
            "**Bold, clean outlines on a stark white background**, resembling a simple coloring book page. "
            "Includes basic, engaging background elements like grass, sky, and playful sports equipment, framed to enhance the main subject. "
            "Details suitable for kids. Pixel dimensions: **685px width, 913px height (3:4 aspect ratio)**. "
            "**No grayscale, no shading, no color fill whatsoever.**"
        )
        
        negative_prompt = (
            "color, grayscale, shading, shadows, gradients, textures, photorealistic, 3D, complex, "
            "ugly, disfigured, scary, boring, dull, muted, abstract, text, signature, watermark, logo, "
            "multiple subjects, small subject, too much white space, empty background"
        )
        
        # Use Gemini 2.5 Flash for image generation
        model = genai.GenerativeModel('models/gemini-2.5-flash-image-preview')
        
        # Create the full prompt with negative examples
        full_prompt = f"{image_generation_prompt}\n\nNegative: {negative_prompt}"
        
        logger.info("Sending prompt to Gemini API for image generation")
        response = model.generate_content(full_prompt)
        
        # Extract image data from response
        image_data = None
        resp_text = None
        
        try:
            if hasattr(response, 'to_dict'):
                try:
                    resp_text = json.dumps(response.to_dict())
                except Exception:
                    resp_text = str(response)
            else:
                resp_text = str(response)
            
            # Look for data URLs like: data:image/png;base64,AAAA...
            data_url_pattern = re.compile(r'data:(image/[^;]+);base64,([A-Za-z0-9+/=\n\r]+)')
            m = data_url_pattern.search(resp_text)
            
            if m:
                mime_type = m.group(1)
                b64_data = re.sub(r'\s+', '', m.group(2))
                image_data = base64.b64decode(b64_data)
                logger.info(f"Extracted image data from response (mime: {mime_type})")
            else:
                # Try to find long standalone base64 blocks (heuristic)
                long_b64_pattern = re.compile(r'([A-Za-z0-9+/=\n\r]{800,})')
                m2 = long_b64_pattern.search(resp_text)
                if m2:
                    b64_data = re.sub(r'\s+', '', m2.group(1))
                    try:
                        image_data = base64.b64decode(b64_data)
                        logger.info("Extracted image data using heuristic base64 pattern")
                    except Exception as e:
                        logger.error(f"Failed to decode heuristic base64 data: {e}")
        
        except Exception as e:
            logger.error(f"Error extracting image from response: {e}")
        
        if not image_data:
            raise Exception("No image data found in API response")
        
        # Save image to disk
        if output_dir is None:
            output_dir = Path(settings.MEDIA_ROOT) / 'image'
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        image_filename = f"genai_response_{timestamp}.png"
        image_path = output_dir / image_filename
        
        # Save the PNG image
        with open(image_path, 'wb') as f:
            f.write(image_data)
        
        logger.info(f"Saved generated image to: {image_path}")
        
        # Generate raw image data for printer
        image_raw_data = _generate_raw_image_data(image_path)
        
        return str(image_path), image_raw_data
    
    except Exception as e:
        logger.error(f"Error during image generation: {str(e)}")
        raise


def _generate_raw_image_data(image_path: str) -> bytes:
    """
    Convert an image to raw binary data suitable for the printer.
    
    Process:
    1. Load the image
    2. Resize to 48 bytes per row (384 pixels), preserving aspect ratio
    3. Convert to 1-bit using Floyd-Steinberg dithering
    4. Pack into raw bytes (row-major, LSB-first)
    
    Args:
        image_path: Full path to the image file
    
    Returns:
        bytes: Raw binary data for the printer
    """
    from PIL import Image
    
    try:
        logger.info(f"Generating raw image data from: {image_path}")
        
        with Image.open(image_path) as img:
            # Bytes per row requested by the printer
            width_bytes = 48
            width_px = width_bytes * 8  # 384 pixels
            
            orig_w, orig_h = img.size
            # Preserve aspect ratio: compute new height for width_px
            new_w = width_px
            new_h = max(1, int(orig_h * (new_w / orig_w)))
            
            # Resize and dither (Floyd-Steinberg)
            gray = img.resize((new_w, new_h), resample=Image.LANCZOS).convert('L')
            bw = gray.convert('1')  # default uses Floyd-Steinberg dither
            
            # Pack into raw bytes (LSB-first per row)
            raw = bytearray()
            for y in range(new_h):
                byte = 0
                bits = 0
                for x in range(new_w):
                    pixel = bw.getpixel((x, y))
                    # pixel is 0 (black) or 255 (white)
                    bit = 1 if pixel == 0 else 0
                    # Invert bit for printer (default behavior)
                    bit ^= 1
                    # LSB-first: place bit at current bit position (0..7)
                    byte |= (bit << bits)
                    bits += 1
                    if bits == 8:
                        raw.append(byte & 0xFF)
                        byte = 0
                        bits = 0
                if bits > 0:
                    # Leftover bits are already in low-order positions; pad high bits with 0
                    raw.append(byte & 0xFF)
            
            # Ensure row length
            expected_len = new_h * width_bytes
            if len(raw) != expected_len:
                logger.warning(f"Raw length {len(raw)} does not match expected {expected_len}; adjusting")
                if len(raw) > expected_len:
                    raw = raw[:expected_len]
                else:
                    raw.extend(b'\x00' * (expected_len - len(raw)))
            
            logger.info(f"Generated raw image data: {len(raw)} bytes ({new_w}x{new_h} pixels)")
            return bytes(raw)
    
    except Exception as e:
        logger.error(f"Error generating raw image data: {e}")
        raise
