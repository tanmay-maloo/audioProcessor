#!/usr/bin/env python3
"""
visualize_raw.py

Read a raw binary file (row-major, 48 bytes per row) and save a viewable PNG.

Usage:
  python tools/visualize_raw.py path/to/file.bin --width-bytes 48 --out out.png
"""
from pathlib import Path
from PIL import Image
import argparse


def main():
    p = argparse.ArgumentParser()
    p.add_argument('input', type=Path)
    p.add_argument('--width-bytes', type=int, default=48)
    p.add_argument('--out', type=Path, default=None)
    p.add_argument('--invert', action='store_true', help='Invert bits when visualizing')
    args = p.parse_args()

    inp = args.input
    if not inp.exists():
        print(f"Input not found: {inp}")
        return

    data = inp.read_bytes()
    width = args.width_bytes * 8
    # compute height
    if len(data) % args.width_bytes != 0:
        print(f"Warning: data length {len(data)} not a multiple of width_bytes {args.width_bytes}")
    height = len(data) // args.width_bytes

    img = Image.new('1', (width, height))
    idx = 0
    for y in range(height):
        for bx in range(args.width_bytes):
            byte = data[idx]
            idx += 1
            for bit in range(8):
                # MSB-first
                bit_val = (byte & (1 << (7 - bit))) != 0
                if args.invert:
                    bit_val = not bit_val
                # In this raw format, 1 means black; convert to pixel: True->black(0)
                pixel = 0 if bit_val else 255
                x = bx * 8 + bit
                img.putpixel((x, y), pixel)

    out = args.out if args.out else inp.with_suffix('.visualized.png')
    img.save(out)
    print(f"Saved visualization: {out} ({out.stat().st_size} bytes) w={width} h={height}")


if __name__ == '__main__':
    main()
