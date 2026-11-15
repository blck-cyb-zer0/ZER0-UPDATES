#!/usr/bin/env python3
# ZERO Auto Subtitle Downloader - Finds subtitles for ANY movie automatically
# Uses OpenSubtitles API via subliminal: pip install subliminal
import os, glob
from pathlib import Path

print("=== ZERO Auto Subtitle Downloader ===")
print("Put your movie in SAME folder as this script.")
print("It will download English subtitle next to the movie.\n")

try:
    from subliminal import download_best_subtitles, save_subtitles, Video
except ImportError:
    print("First time? Install this once:")
    print("pip install subliminal")
    print("\nAlternative: If that fails, search the movie name on subscene.com")
    input("Press Enter to close...")
    exit()

videos = []
for ext in ["*.mp4", "*.mkv", "*.avi", "*.mov", "*.webm"]:
    videos.extend(glob.glob(ext))

if not videos:
    print("No video found. Put your movie file here and run again.")
else:
    for v in videos:
        print(f"Searching subtitle for: {v}")
        try:
            video = Video.fromname(v)
            subs = download_best_subtitles([video], languages={"en"})
            if subs[video]:
                save_subtitles(video, subs[video])
                print(f" DONE! Subtitle saved next to {v}")
            else:
                print(" No subtitle found for this one.")
        except Exception as e:
            print(f" Error: {e}")

print("\nTip: Rename movie to correct name like 'Avatar.2.2022.mp4' for better match.")
input("\nPress Enter to close...")
