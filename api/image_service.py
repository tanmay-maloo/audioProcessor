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

# Flag to enable/disable AI-based subject classification
USE_AI_CLASSIFICATION = os.getenv('USE_AI_CLASSIFICATION', 'true').lower() == 'true'


def classify_subject_with_ai(text_subject: str) -> str:
    """
    Use AI to classify the subject into a category for prompt optimization.
    
    Args:
        text_subject: The transcribed text describing what to draw
    
    Returns:
        str: Category - either 'text' or 'object'
            - 'text': Single letters, numbers, greetings, text-based designs
            - 'object': Physical objects, animals, people, scenes
    """
    try:
        from google import genai
        
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            logger.warning("GOOGLE_API_KEY not set, defaulting to 'object' category")
            return 'object'
        
        client = genai.Client(api_key=api_key)
        
        classification_prompt = (
            f"Classify this drawing request into ONE category:\n"
            f"Request: '{text_subject}'\n\n"
            f"Categories:\n"
            f"- 'text': Single letters (A-Z), numbers (0-9), greetings (Happy Birthday, Congratulations), "
            f"text-based designs, or requests to draw text/letters/numbers\n"
            f"- 'object': Physical objects, animals, people, vehicles, food, scenes, or anything drawable as an illustration\n\n"
            f"Respond with ONLY ONE WORD: either 'text' or 'object'"
        )
        
        # Use a fast text model for classification (not image generation)
        classification_model = os.getenv('GEMINI_TEXT_MODEL', 'gemini-2.0-flash')
        
        logger.info(f"🔍 Classifying subject with AI using {classification_model}")
        start_time = datetime.utcnow()
        
        response = client.models.generate_content(
            model=classification_model,
            contents=[classification_prompt]
        )
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Extract the classification from response
        classification = response.text.strip().lower()
        
        # Validate response
        if classification not in ['text', 'object']:
            logger.warning(f"Invalid AI classification response: '{classification}', defaulting to 'object'")
            classification = 'object'
        
        logger.info(f"✅ AI classified '{text_subject}' as '{classification}' in {duration:.2f}s")
        return classification
        
    except Exception as e:
        logger.error(f"Error in AI classification: {e}, defaulting to 'object'")
        return 'object'


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
        logger.info(f"⏱️  [TIMING] Starting image generation for subject: {text_subject}")
        
        # Record overall start time
        overall_start_time = datetime.utcnow()
        
        # Record classification start time
        classification_start_time = datetime.utcnow()
        
        # Analyze the subject to determine the appropriate prompt type
        if USE_AI_CLASSIFICATION:
            # Use AI to classify the subject
            category = classify_subject_with_ai(text_subject)
            is_text_based = (category == 'text')
        else:
            # Default to object-based (non-text) when AI classification is disabled
            # This ensures we always generate illustrations unless AI explicitly says it's text
            is_text_based = False
            logger.info(f"AI classification disabled, defaulting to 'object' category")
        
        classification_end_time = datetime.utcnow()
        classification_duration = (classification_end_time - classification_start_time).total_seconds()
        logger.info(f"⏱️  [TIMING] Subject classification completed in {classification_duration:.2f}s")
        
        # Build the prompt based on the case
        if is_text_based:
            # Case 1: Decorative text/lettering
            case_specific_rule = (
                f"Large, bold, decorative lettering of what is requested in this message '{text_subject}' fills 60-70% of canvas. "
                "Playful, bubbly font with decorative flourishes. "
                "Themed background elements (balloons, stars, confetti, flowers) fill entire frame edge to edge."
            )
        else:
            # Case 2: Physical object/scene with contextual background
            case_specific_rule = (
                f"Main subject '{text_subject}' large and centered, filling 60-70% of frame. "
                "Complete contextual background fills ENTIRE image edge to edge: "
                "animals get habitat (ground, trees, sky, flowers); "
                "vehicles get road scene (buildings, clouds, signs); "
                "food gets kitchen/dining (table, utensils); "
                "people get full environment (ground, buildings/nature, sky). "
                "Layer: foreground (subject), middle ground (related objects), background (sky, clouds)."
            )
        
        # Always-applied rules (consistent across all cases)
        always_rules = (
            "Kid-friendly cartoon style. Thick black outlines (3-5px). Solid white fill. "
            "Pure black and white only - no grayscale, shading, gradients, or color. "
            "Clean coloring book aesthetic. No border around image - scene extends to edges. "
            "3:4 aspect ratio (685x913px)."
        )
        
        # Combine into final prompt
        image_generation_prompt = f"{case_specific_rule} {always_rules}"
        
        negative_prompt = (
            "color, grayscale, shading, gradients, blur, photorealistic, 3D, "
            "thin lines, sketchy, dithered, low contrast, complex details, "
            "ugly, distorted, overcrowded, empty background, subject too small, border around image"
        )
        # Use specified model or get from environment or default
        if model_name is None:
            model_name = os.getenv('GEMINI_IMAGE_MODEL', 'gemini-2.5-flash-image')
        
        logger.info(f"Using model: {model_name}")
        
        # Create client with API key
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise Exception("GOOGLE_API_KEY environment variable is not set")
        
        client_init_start = datetime.utcnow()
        client = genai.Client(api_key=api_key)
        client_init_end = datetime.utcnow()
        client_init_duration = (client_init_end - client_init_start).total_seconds()
        logger.info(f"⏱️  [TIMING] Gemini client initialization: {client_init_duration:.2f}s")
        
        # Create the full prompt with negative examples
        full_prompt = f"{image_generation_prompt}\n\nNegative: {negative_prompt}"
        
        logger.info(f"⏱️  [TIMING] Sending prompt to Gemini API for image generation")
        api_call_start = datetime.utcnow()
        
        response = client.models.generate_content(
            model=model_name,
            contents=[full_prompt],
        )
        
        # Record API call end time
        api_end_time = datetime.utcnow()
        api_duration = (api_end_time - api_call_start).total_seconds()
        total_api_duration = (api_end_time - client_init_start).total_seconds()
        logger.info(f"⏱️  [TIMING] Gemini API call completed in {api_duration:.2f}s (total with init: {total_api_duration:.2f}s)")
        
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
        logger.info(f"⏱️  [TIMING] Image data extraction completed in {processing_duration:.2f}s")
        
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
        pil_load_start = datetime.utcnow()
        original_image = Image.open(io.BytesIO(image_data))
        pil_load_end = datetime.utcnow()
        pil_load_duration = (pil_load_end - pil_load_start).total_seconds()
        
        original_size = len(image_data)
        logger.info(f"Original image size: {original_image.size}, file size: {original_size / 1024:.2f} KB")
        logger.info(f"⏱️  [TIMING] PIL image load: {pil_load_duration:.2f}s")
        
        # Scale down the image to reduce file size while maintaining aspect ratio
        # Target max dimension of 600px (ideal for 58mm thermal printer)
        resize_start = datetime.utcnow()
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
        
        resize_end = datetime.utcnow()
        resize_duration = (resize_end - resize_start).total_seconds()
        logger.info(f"⏱️  [TIMING] Image resize: {resize_duration:.2f}s")
        
        # Convert to grayscale for black/white line art (reduces file size significantly)
        # 'L' mode = 8-bit grayscale, perfect for thermal printer output
        convert_start = datetime.utcnow()
        grayscale_image = scaled_image.convert('L')
        logger.info(f"Converted to grayscale mode for optimal thermal printing")
        
        # Strip metadata to reduce file size
        # Remove EXIF, ICC profile, and other metadata
        data = list(grayscale_image.getdata())
        image_without_exif = Image.new('L', grayscale_image.size)
        image_without_exif.putdata(data)
        convert_end = datetime.utcnow()
        convert_duration = (convert_end - convert_start).total_seconds()
        logger.info(f"⏱️  [TIMING] Grayscale conversion & metadata strip: {convert_duration:.2f}s")
        
        # Save with maximum PNG compression while maintaining quality
        # compress_level=9 provides maximum compression (0-9 scale)
        # optimize=True enables additional compression passes
        png_save_start = datetime.utcnow()
        image_without_exif.save(image_path, 'PNG', optimize=True, compress_level=9)
        png_save_end = datetime.utcnow()
        png_save_duration = (png_save_end - png_save_start).total_seconds()
        
        # Get final file size
        final_size = os.path.getsize(image_path)
        compression_ratio = (1 - final_size / original_size) * 100 if original_size > 0 else 0
        
        # Record file save end time
        save_end_time = datetime.utcnow()
        save_duration = (save_end_time - save_start_time).total_seconds()
        
        logger.info(f"Saved scaled image to: {image_path}")
        logger.info(f"Final file size: {final_size / 1024:.2f} KB (reduced by {compression_ratio:.1f}%)")
        logger.info(f"⏱️  [TIMING] PNG save with compression: {png_save_duration:.2f}s")
        logger.info(f"⏱️  [TIMING] Total file save operations: {save_duration:.2f}s")
        
        # Generate raw image data for printer
        raw_start_time = datetime.utcnow()
        image_raw_data = _generate_raw_image_data(image_path)
        raw_end_time = datetime.utcnow()
        raw_duration = (raw_end_time - raw_start_time).total_seconds()
        
        # Calculate overall duration
        overall_end_time = datetime.utcnow()
        total_duration = (overall_end_time - overall_start_time).total_seconds()
        
        # Log detailed breakdown
        logger.info(f"⏱️  [TIMING] Raw image processing completed in {raw_duration:.2f}s")
        logger.info(f"⏱️  [TIMING] ═══════════════════════════════════════════════════════")
        logger.info(f"⏱️  [TIMING] 📊 IMAGE GENERATION BREAKDOWN:")
        logger.info(f"⏱️  [TIMING]   • Classification:       {classification_duration:6.2f}s ({(classification_duration/total_duration)*100:5.1f}%)")
        logger.info(f"⏱️  [TIMING]   • Gemini API call:      {total_api_duration:6.2f}s ({(total_api_duration/total_duration)*100:5.1f}%)")
        logger.info(f"⏱️  [TIMING]   • Image extraction:     {processing_duration:6.2f}s ({(processing_duration/total_duration)*100:5.1f}%)")
        logger.info(f"⏱️  [TIMING]   • File save operations: {save_duration:6.2f}s ({(save_duration/total_duration)*100:5.1f}%)")
        logger.info(f"⏱️  [TIMING]   • Raw data generation:  {raw_duration:6.2f}s ({(raw_duration/total_duration)*100:5.1f}%)")
        logger.info(f"⏱️  [TIMING]   ─────────────────────────────────────────────────")
        logger.info(f"⏱️  [TIMING]   ⭐ TOTAL:               {total_duration:6.2f}s (100.0%)")
        logger.info(f"⏱️  [TIMING] ═══════════════════════════════════════════════════════")
        
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