#!/usr/bin/env python3
"""
reduce_image.py

Small utility to resize a PNG, convert to 1-bit (monochrome) and export
both a compact PNG and a raw binary array suitable for embedded displays.

Usage:
  python tools/reduce_image.py /path/to/input.png --rows 600 --width 48

Outputs:
  - <input>_reduced.png  : the resized 1-bit PNG
  - <input>_reduced.bin  : raw bytes, row-major, each row padded to full bytes

This script uses Pillow (PIL). Install with: pip install Pillow
"""
import argparse
from pathlib import Path
from PIL import Image


def image_to_1bit_raw(img: Image.Image, height: int, width: int) -> tuple[bytes, Image.Image]:
    # Ensure size
    img = img.convert('L')
    img = img.resize((width, height), resample=Image.LANCZOS)
    # Convert to 1-bit using a threshold (128)
    bw = img.point(lambda p: 255 if p > 128 else 0, mode='1')

    # Get raw data: each row packed into bytes (MSB first)
    raw = bytearray()
    for y in range(height):
        row_bits = 0
        bits_count = 0
        for x in range(width):
            pixel = bw.getpixel((x, y))
            bit = 0 if pixel else 1  # Treat black (0) as 1 so set bit for dark pixels
            row_bits = (row_bits << 1) | bit
            bits_count += 1
            if bits_count == 8:
                raw.append(row_bits & 0xFF)
                row_bits = 0
                bits_count = 0
        # pad remaining bits in the row (if width not multiple of 8)
        if bits_count > 0:
            row_bits = row_bits << (8 - bits_count)
            raw.append(row_bits & 0xFF)

    return bytes(raw), bw


def find_size_meeting_target(img: Image.Image, target_bytes: int, min_width: int = 8, min_height: int = 8) -> tuple[int, int, bytes, Image.Image]:
    """Reduce dimensions progressively until produced PNG size is <= target_bytes.

    Strategy: start from original size, scale down by a factor until the saved 1-bit PNG is <= target.
    We'll try reducing by 10% steps, and stop at min dimensions to avoid degenerate outputs.
    Returns (height, width, raw_bytes, bw_image)
    """
    orig_w, orig_h = img.size
    # Start from original width but cap width to orig if necessary; we'll maintain aspect ratio
    w = orig_w
    h = orig_h

    # If width < 8, force to 8 to avoid zero-byte rows
    w = max(w, min_width)
    h = max(h, min_height)

    # Try loop
    while True:
        # Create 1-bit image and test PNG size by saving to bytes
        test_img = img.resize((w, h), resample=Image.LANCZOS).convert('L').point(lambda p: 255 if p > 128 else 0, mode='1')
        from io import BytesIO

        buf = BytesIO()
        test_img.save(buf, format='PNG', bits=1)
        size = buf.tell()
        if size <= target_bytes or (w <= min_width or h <= min_height):
            # produce raw bytes as well
            raw, bw = image_to_1bit_raw(img, h, w)
            return h, w, raw, bw

        # reduce by 10% and repeat
        w = max(min_width, int(w * 0.9))
        h = max(min_height, int(h * 0.9))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('input', type=Path)
    p.add_argument('--rows', type=int, default=None, help='Explicit height in pixels (overrides auto)')
    p.add_argument('--width', type=int, default=None, help='Explicit width in pixels (overrides auto)')
    p.add_argument('--target-bytes', type=int, default=50_000, help='Target max size for the 1-bit PNG (default: 50KB)')
    p.add_argument('--threshold', type=int, default=128)
    p.add_argument('--min-width', type=int, default=8)
    p.add_argument('--min-height', type=int, default=8)
    args = p.parse_args()

    inp = args.input
    if not inp.exists():
        print(f"Input not found: {inp}")
        return

    img = Image.open(inp)

    # If explicit size provided, use that; otherwise auto-reduce to target-bytes
    if args.rows and args.width:
        height = args.rows
        width = args.width
        raw, bw = image_to_1bit_raw(img, height, width)
    else:
        height, width, raw, bw = find_size_meeting_target(img, args.target_bytes, min_width=args.min_width, min_height=args.min_height)

        # Ensure raw binary (uncompressed) also respects roughly the same target.
        # Compute max bytes per row allowed to keep raw <= target
        import math
        max_bytes_per_row = max(1, args.target_bytes // max(1, height))
        max_width_for_raw = max(1, max_bytes_per_row * 8)
        if width > max_width_for_raw:
            # Reduce width to fit raw budget, rounding down to nearest multiple of 8
            new_width = (max_width_for_raw // 8) * 8
            new_width = max(new_width, args.min_width)
            if new_width < width:
                width = new_width
                raw, bw = image_to_1bit_raw(img, height, width)

    out_png = inp.with_name(inp.stem + '_reduced.png')
    out_bin = inp.with_name(inp.stem + '_reduced.bin')

    # Save the 1-bit PNG
    bw.save(out_png, bits=1)
    # Save raw binary
    out_bin.write_bytes(raw)

    print(f"Saved reduced PNG: {out_png} ({out_png.stat().st_size} bytes)")
    print(f"Saved raw bin: {out_bin} ({out_bin.stat().st_size} bytes)")


if __name__ == '__main__':
    main()
