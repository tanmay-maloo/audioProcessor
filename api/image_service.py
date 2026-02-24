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
        # image_generation_prompt = (
        #     f"A cheerful, kid-friendly cartoon-style **pure black line art drawing** of a {text_subject}. "
        #     "**Subject is large and fills the canvas well**, with an expressive face, varied hairstyles, and dynamic pose. "
        #     "**Bold, clean outlines on a stark white background**, resembling a simple coloring book page. "
        #     "Includes basic, engaging background elements like grass, sky, and playful sports equipment, framed to enhance the main subject. "
        #     "Details suitable for kids. Pixel dimensions: **685px width, 913px height (3:4 aspect ratio)**. "
        #     "**No grayscale, no shading, no color fill whatsoever.**"
        # )
        
        # negative_prompt = (
        #     "color, grayscale, shading, shadows, gradients, textures, photorealistic, 3D, complex, "
        #     "ugly, disfigured, scary, boring, dull, muted, abstract, text, signature, watermark, logo, "
        #     "multiple subjects, small subject, too much white space, empty background"
        # )
        # Detect if this is a text-based greeting/message (no clear physical subject)
        text_keywords = ['happy', 'congratulations', 'welcome', 'birthday', 'diwali', 'christmas', 
                        'new year', 'thank you', 'good luck', 'best wishes', 'celebration']
        is_text_greeting = any(keyword in text_subject.lower() for keyword in text_keywords)
        
        if is_text_greeting:
            # For greetings/messages: create bold decorative text with themed background
            image_generation_prompt = (
                f"A bold, high-contrast black and white decorative design featuring the text: '{text_subject}'. "
                "Large, bold, decorative hand-lettered text fills 50-60% of the center with thick outlines (4-6px width). "
                "Text style: playful, bubbly, kid-friendly font with decorative flourishes. "
                "IMPORTANT: Include a COMPLETE themed background scene that fills the ENTIRE image from edge to edge, "
                "related to the message theme: "
                "if Diwali - diyas, rangoli patterns, fireworks, decorative lamps, stars; "
                "if Christmas - trees, ornaments, snowflakes, gifts, bells, stars; "
                "if Birthday - balloons, confetti, cake, candles, party hats, streamers; "
                "if celebration - fireworks, stars, confetti, balloons, decorative elements; "
                "if nature theme - flowers, leaves, vines, butterflies, clouds, sun. "
                "Background decorative elements should fill 100% of the frame around the text. "
                "Each element has its own outline, but NO border or frame around the entire image. "
                "Pure black lines on white fill only - no grayscale, no shading, no gradients, no color. "
                "Clean vector-style coloring book aesthetic with bold, simplified shapes suitable for thermal printing. "
                "Composition: 3:4 aspect ratio (685x913px)."
            )
        else:
            # For object-based subjects: create scene with main subject
            image_generation_prompt = (
                f"A bold, high-contrast black and white illustration of: {text_subject}. "
                "Kid-friendly cartoon style with thick, chunky black outlines (3-5px width) around each individual object and solid white fill areas. "
                "Main subject is large and centered, filling 60-70% of the frame with an expressive, cheerful appearance. "
                "IMPORTANT: Include a COMPLETE contextual background scene that fills the ENTIRE image from edge to edge: "
                "if playing/sports - full playground scene with ground, sky, clouds, other kids playing, equipment, grass, sun; "
                "if animal - complete natural habitat with ground/grass, trees, bushes, clouds, sky, flowers, other small animals; "
                "if food - full kitchen or dining scene with table, plates, utensils, windows, decorations; "
                "if vehicle - complete road/street scene with buildings, trees, clouds, road markings, traffic signs, landscape; "
                "if character/person - full environment scene with ground, buildings or nature, sky with clouds or sun. "
                "Background should fill 100% of the frame with simplified line art elements creating a complete scene. "
                "Layer the scene: foreground (main subject), middle ground (related objects), background (sky, clouds, distant elements). "
                "Each object has its own outline, but NO border or frame around the entire image - the scene extends to all edges. "
                "Pure black lines on white fill only - no grayscale, no shading, no gradients, no color. "
                "Clean vector-style coloring book aesthetic with bold, simplified shapes suitable for thermal printing. "
                "Composition: 3:4 aspect ratio (685x913px), front-facing or 3/4 view angle for consistency."
            )

        negative_prompt = (
            "color, colored, grayscale, gray tones, shading, shadows, gradients, soft edges, blur, "
            "photorealistic, 3D render, realistic textures, detailed textures, crosshatching, stippling, "
            "thin lines, sketchy lines, messy lines, dithered patterns, halftone dots, "
            "low contrast, faded, washed out, complex details, intricate patterns, "
            "scary, ugly, disfigured, distorted, too many subjects, overcrowded, cluttered, "
            "empty background, plain white background, blank background, too much white space, subject too small, "
            "border around image, frame around sticker, outer border, rectangular border, edge border, sticker outline"
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
        
        # Load image with PIL to scale it down
        # Open the image from bytes
        original_image = Image.open(io.BytesIO(image_data))
        original_size = len(image_data)
        logger.info(f"Original image size: {original_image.size}, file size: {original_size / 1024:.2f} KB")
        
        # Scale down the image to reduce file size while maintaining aspect ratio
        # Target max dimension of 600px (ideal for 58mm thermal printer)
        max_dimension = 600
        width, height = original_image.size
        
        if width > max_dimension or height > max_dimension:
            # Calculate scaling factor
            scale_factor = min(max_dimension / width, max_dimension / height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            
            # Resize with high-quality resampling
            scaled_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"Scaled image from {original_image.size} to {scaled_image.size}")
        else:
            scaled_image = original_image
            logger.info("Image already within size limits, no scaling needed")
        
        # Convert to grayscale for black/white line art (reduces file size significantly)
        # 'L' mode = 8-bit grayscale, perfect for thermal printer output
        grayscale_image = scaled_image.convert('L')
        logger.info(f"Converted to grayscale mode for optimal thermal printing")
        
        # Strip metadata to reduce file size
        # Remove EXIF, ICC profile, and other metadata
        data = list(grayscale_image.getdata())
        image_without_exif = Image.new('L', grayscale_image.size)
        image_without_exif.putdata(data)
        
        # Save with maximum PNG compression while maintaining quality
        # compress_level=9 provides maximum compression (0-9 scale)
        # optimize=True enables additional compression passes
        image_without_exif.save(image_path, 'PNG', optimize=True, compress_level=9)
        
        # Get final file size
        final_size = os.path.getsize(image_path)
        compression_ratio = (1 - final_size / original_size) * 100 if original_size > 0 else 0
        
        # Record file save end time
        save_end_time = datetime.utcnow()
        save_duration = (save_end_time - save_start_time).total_seconds()
        
        logger.info(f"Saved scaled image to: {image_path}")
        logger.info(f"Final file size: {final_size / 1024:.2f} KB (reduced by {compression_ratio:.1f}%)")
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