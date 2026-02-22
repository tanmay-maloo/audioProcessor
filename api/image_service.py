"""
Image Generation Service using Google Generative AI
This module handles image generation based on transcribed text.
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


def create_and_save_image(text_subject: str, output_dir: str = None, model_name: str = None) -> tuple:
    """
    Generate an image from text using Google Generative AI and save it locally.
    Also returns the raw image data for the printer.
    
    Args:
        text_subject: The subject/description for the image
        output_dir: Directory to save the image (defaults to media/image/)
        model_name: Specific model to use (defaults to gemini-2.5-flash-image)
    
    Returns:
        tuple: (image_path, image_raw_data) where:
            - image_path: Full path to the saved PNG image
            - image_raw_data: Binary data of the processed image for printer
    """
    from django.conf import settings
    from PIL import Image
    import io
    
    try:
        # Import the new Google GenAI SDK
        from google import genai
        
        logger.info(f"Starting image generation for subject: {text_subject}")
        
        # Record API call start time
        api_start_time = datetime.utcnow()
        
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
        
        # Use specified model or get from environment or default
        if model_name is None:
            model_name = os.getenv('GEMINI_IMAGE_MODEL', 'gemini-2.5-flash-image')
        
        logger.info(f"Using model: {model_name}")
        
        # Create client with API key
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise Exception("GOOGLE_API_KEY environment variable is not set")
        
        client = genai.Client(api_key=api_key)
        
        # Create the full prompt with negative examples
        full_prompt = f"{image_generation_prompt}\n\nNegative: {negative_prompt}"
        
        logger.info("Sending prompt to Gemini API for image generation")
        response = client.models.generate_content(
            model=model_name,
            contents=[full_prompt],
        )
        
        # Record API call end time
        api_end_time = datetime.utcnow()
        api_duration = (api_end_time - api_start_time).total_seconds()
        logger.info(f"Gemini API call completed in {api_duration:.2f}s")
        
        # Record image processing start time
        processing_start_time = datetime.utcnow()
        
        # Extract image data from response
        image_data = None
        
        try:
            # The new API returns parts with inline_data
            for part in response.parts:
                if part.inline_data is not None:
                    # Get the image data directly (it's already bytes)
                    image_data = part.inline_data.data
                    logger.info("Extracted image data from response parts")
                    break
                elif part.text is not None:
                    logger.info(f"Response text: {part.text}")
        
        except Exception as e:
            logger.error(f"Error extracting image from response: {e}")
        
        if not image_data:
            raise Exception("No image data found in API response")
        
        # Record image processing end time
        processing_end_time = datetime.utcnow()
        processing_duration = (processing_end_time - processing_start_time).total_seconds()
        logger.info(f"Image data extraction completed in {processing_duration:.2f}s")
        
        # Record file save start time
        save_start_time = datetime.utcnow()
        
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
        
        # Record file save end time
        save_end_time = datetime.utcnow()
        save_duration = (save_end_time - save_start_time).total_seconds()
        
        logger.info(f"Saved generated image to: {image_path}")
        logger.info(f"File save completed in {save_duration:.2f}s")
        
        # Generate raw image data for printer
        raw_start_time = datetime.utcnow()
        image_raw_data = _generate_raw_image_data(image_path)
        raw_end_time = datetime.utcnow()
        raw_duration = (raw_end_time - raw_start_time).total_seconds()
        
        # Log detailed breakdown
        total_duration = (raw_end_time - api_start_time).total_seconds()
        logger.info(f"Raw image processing completed in {raw_duration:.2f}s")
        logger.info(f"Image generation breakdown - API: {api_duration:.2f}s, Processing: {processing_duration:.2f}s, Save: {save_duration:.2f}s, Raw: {raw_duration:.2f}s, Total: {total_duration:.2f}s")
        
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
    5. Store WITHOUT inversion (invert=False) so endpoints can apply inversion as needed
    
    Args:
        image_path: Full path to the image file
    
    Returns:
        bytes: Raw binary data for the printer (NOT inverted)
    """
    from datetime import datetime
    from .image_utils import generate_raw_image_data
    
    try:
        logger.info(f"Generating raw image data from: {image_path}")
        
        # Record raw processing start time
        start_time = datetime.utcnow()
        
        # Use common utility function with invert=False
        # This stores the data in non-inverted form, allowing endpoints to apply inversion as needed
        raw_data = generate_raw_image_data(image_path, invert=False)
        
        # Record and log processing time
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Raw image data generation took {duration:.2f}s")
        
        return raw_data
    
    except Exception as e:
        logger.error(f"Error generating raw image data: {e}")
        raise