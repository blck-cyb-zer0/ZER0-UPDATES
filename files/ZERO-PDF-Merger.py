#!/usr/bin/env python3
# ZERO PDF Merger / Unlocker - Works offline, unlimited, no data stolen
# Needs: pip install pypdf
import os, glob, sys

print("=== ZERO PDF Merger / Unlocker ===")
print("Put all PDFs you want to merge in SAME folder as this script.")
print("It will merge them in alphabetical order.\n")

try:
    from pypdf import PdfWriter, PdfReader
except ImportError:
    print("First time? Install this once:")
    print("pip install pypdf")
    input("Press Enter to close...")
    sys.exit()

pdfs = sorted(glob.glob("*.pdf"))
# Don't merge the output itself
pdfs = [p for p in pdfs if p.lower() != "merged.pdf"]

if not pdfs:
    print("No PDFs found in this folder. Drag PDFs here and run again.")
else:
    print(f"Found {len(pdfs)} PDFs:")
    for p in pdfs:
        print(f" - {p}")

    writer = PdfWriter()
    for p in pdfs:
        try:
            reader = PdfReader(p)
            if reader.is_encrypted:
                print(f"{p} is locked, trying empty password...")
                try:
                    reader.decrypt("")
                except:
                    print(f"Skipped {p} - needs password")
                    continue
            for page in reader.pages:
                writer.add_page(page)
        except Exception as e:
            print(f"Skipped {p}: {e}")

    with open("merged.pdf", "wb") as f:
        writer.write(f)
    print("\nDONE! Saved as merged.pdf")

input("\nPress Enter to close...")
