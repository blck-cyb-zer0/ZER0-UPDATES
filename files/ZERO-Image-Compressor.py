#!/usr/bin/env python3
# ZERO Bulk Image Compressor - Compress 100 images, keep quality at 90%
# Needs: pip install Pillow
import os
from pathlib import Path

print("=== ZERO Bulk Image Compressor ===")
print("Put images in a folder called 'images' next to this script.")
print("Compressed images go to 'compressed' folder. Originals NOT touched.\n")

try:
    from PIL import Image
except ImportError:
    print("First time? Install this once: pip install Pillow")
    input("Press Enter to close...")
    exit()

src = Path("images")
dst = Path("compressed")
dst.mkdir(exist_ok=True)

if not src.exists():
    src.mkdir(exist_ok=True)
    print("Created 'images' folder. Put your JPG/PNG/WebP inside and run again.")
    input("Press Enter to close...")
    exit()

print("Quality: 1=Small (60%)  2=Medium (80%)  3=High (90%)")
choice = input("Choose 1/2/3 [default 3]: ").strip() or "3"
quality = {"1": 60, "2": 80, "3": 90}.get(choice, 90)

count = 0
for file in src.glob("*"):
    if file.suffix.lower() not in [".jpg", ".jpeg", ".png", ".webp"]:
        continue
    try:
        img = Image.open(file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        out = dst / file.name
        img.save(out, optimize=True, quality=quality)
        before = file.stat().st_size / 1024
        after = out.stat().st_size / 1024
        print(f"{file.name}: {before:.0f} KB -> {after:.0f} KB ({100-after/before*100:.0f}% smaller)")
        count += 1
    except Exception as e:
        print(f"Skipped {file.name}: {e}")

print(f"\nDONE! {count} images compressed to 'compressed' folder.")
input("Press Enter to close...")
