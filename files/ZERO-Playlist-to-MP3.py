#!/usr/bin/env python3
# ZERO YouTube Playlist to MP3 Batch Converter
# Needs: pip install yt-dlp  + ffmpeg on your PC
import subprocess, sys, os

print("=== ZERO Playlist to MP3 ===")
print("Paste a YouTube playlist OR single video link.")
print("It will download ALL songs as MP3 320kbps.\n")

url = input("Paste YouTube playlist / video link: ").strip()

if not url:
    print("No link pasted.")
    input("Press Enter to close...")
    sys.exit()

out = os.path.join("MP3 Downloads", "%(playlist_index)s - %(title)s.%(ext)s")
cmd = [
    "yt-dlp",
    "-x", "--audio-format", "mp3", "--audio-quality", "0",
    "--embed-thumbnail", "--add-metadata",
    "-o", out,
    "--yes-playlist",
    url
]

print("\nDownloading... this can take a while for big playlists.\n")
try:
    subprocess.run(cmd)
    print("\nDONE! Check 'MP3 Downloads' folder.")
except FileNotFoundError:
    print("ERROR: yt-dlp not found. Install once: pip install yt-dlp")
    print("And install ffmpeg from https://ffmpeg.org")

input("\nPress Enter to close...")
