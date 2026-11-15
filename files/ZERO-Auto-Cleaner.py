#!/usr/bin/env python3
# ZERO Auto-Cleaner - Frees space safely, no important files deleted
import os, shutil, platform, pathlib

print("=== ZERO Auto-Cleaner ===")
print("Cleans temp, cache, junk. Your documents & photos are NOT touched.\n")

freed = 0
def clean_folder(path, label):
    global freed
    p = pathlib.Path(path).expanduser()
    if not p.exists():
        return
    size = 0
    count = 0
    for root, dirs, files in os.walk(p):
        for f in files:
            fp = os.path.join(root, f)
            try:
                size += os.path.getsize(fp)
                os.remove(fp)
                count += 1
            except:
                pass
    freed += size
    print(f"{label}: cleaned {count} files, freed {size/1024/1024:.1f} MB")

if platform.system() == "Windows":
    clean_folder("~/AppData/Local/Temp", "Windows Temp")
    clean_folder(os.environ.get("TEMP", ""), "System Temp")
    clean_folder("~/AppData/Local/Microsoft/Windows/INetCache", "Browser Cache")
else:
    clean_folder("~/.cache", "Linux Cache")
    clean_folder("/tmp", "Temp (/tmp)")

print(f"\nDONE! Total freed: {freed/1024/1024:.1f} MB")
print("Restart your PC for best result.")
input("Press Enter to close...")
