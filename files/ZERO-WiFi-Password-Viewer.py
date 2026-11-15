#!/usr/bin/env python3
# ZERO WiFi Password Viewer - Shows YOUR OWN saved WiFi passwords
# For Windows: Run as Admin. For Linux: shows NetworkManager saved networks
import subprocess, platform, re, os

print("=== ZERO WiFi Password Viewer ===")
print("Shows only WiFi networks YOUR PC has connected to before.\n")

system = platform.system()

if system == "Windows":
    try:
        out = subprocess.check_output("netsh wlan show profiles", shell=True, text=True, errors="ignore")
        profiles = re.findall(r"All User Profile\s*:\s*(.+)", out)
        if not profiles:
            print("No saved WiFi found.")
        for name in profiles:
            name = name.strip()
            try:
                details = subprocess.check_output(f'netsh wlan show profile name="{name}" key=clear', shell=True, text=True, errors="ignore")
                key = re.search(r"Key Content\s*:\s*(.+)", details)
                print(f"{name}  ->  {key.group(1).strip() if key else '(No password / Open)'}")
            except Exception as e:
                print(f"{name}  ->  Error: {e}")
    except Exception as e:
        print("Run this as Administrator. Error:", e)

elif system == "Linux":
    path = "/etc/NetworkManager/system-connections/"
    if os.path.exists(path):
        for f in os.listdir(path):
            print(f"Found: {f}")
        print("\nTip: Run with sudo to see passwords: sudo cat /etc/NetworkManager/system-connections/YOUR-WIFI.nmconnection")
    else:
        print("No NetworkManager folder found.")

else:
    print("This script is for Windows / Linux PC. On phone, it won't show PC passwords.")

input("\nPress Enter to close...")
