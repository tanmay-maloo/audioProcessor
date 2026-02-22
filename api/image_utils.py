"""
Image processing utilities for raw printer data generation.
This module provides common functions used by multiple endpoints.
"""
import logging
from PIL import Image
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_raw_image_data(image_path: str, invert: bool = True) -> bytes:
    """
    Convert an image to raw binary data suitable for the printer.
    
    This is the canonical function used by all endpoints to ensure consistency.
    
    Process:
    1. Load the image
    2. Resize to 48 bytes per row (384 pixels), preserving aspect ratio
    3. Convert to 1-bit using Floyd-Steinberg dithering
    4. Pack into raw bytes (row-major, LSB-first)
    5. Optionally invert bits based on the invert parameter
    
    Args:
        image_path: Full path to the image file
        invert: Whether to invert bits (True = invert, False = no inversion)
    
    Returns:
        bytes: Raw binary data for the printer
    """
    try:
        logger.info(f"Generating raw image data from: {image_path}, invert={invert}")
        
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
                    
                    # Apply inversion if requested
                    if invert:
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
            
            logger.info(f"Generated raw image data: {len(raw)} bytes ({new_w}x{new_h} pixels), inverted={invert}")
            
            return bytes(raw)
    
    except Exception as e:
        logger.error(f"Error generating raw image data: {e}")
        raise


def flip_bits(data: bytes) -> bytes:
    """
    Flip all bits in the given byte data (0→1, 1→0).
    
    This is used to reverse the inversion of already-processed raw image data.
    
    Args:
        data: Raw byte data
    
    Returns:
        bytes: Data with all bits flipped
    """
    return bytes(b ^ 0xFF for b in data)
