#!/usr/bin/env python3
# ZERO QR Code Maker - make a QR code for a link, some text, or your Wi-Fi so guests can join by scanning.
# Needs: pip install "qrcode[pil]"
from pathlib import Path
import re

OUT = Path("qr-codes")


def pause():
    try:
        input("\nPress Enter to close...")
    except EOFError:
        pass


def wifi_payload(ssid, password, security="WPA", hidden=False):
    """The standard text phones understand for 'join this Wi-Fi'."""
    esc = lambda s: re.sub(r'([\\;,:"])', r"\\\1", s)
    security = security.upper()
    if security not in ("WPA", "WEP", "NOPASS"):
        security = "WPA"
    pw = "" if security == "NOPASS" else f"P:{esc(password)};"
    return f"WIFI:T:{security};S:{esc(ssid)};{pw}{'H:true;' if hidden else ''};"


def safe_name(text):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-")[:40] or "qr"


def main():
    print("=== ZERO QR Code Maker ===")
    try:
        import qrcode
    except ImportError:
        print('First time? Install this once:  pip install "qrcode[pil]"')
        return pause()
    print("1 = Link or text    2 = Wi-Fi network")
    choice = input("Choose 1/2 [default 1]: ").strip() or "1"
    if choice == "2":
        ssid = input("Wi-Fi name: ").strip()
        security = input("Security WPA / WEP / NOPASS [WPA]: ").strip() or "WPA"
        password = "" if security.upper() == "NOPASS" else input("Wi-Fi password: ")
        data, name = wifi_payload(ssid, password, security), "wifi-" + safe_name(ssid)
    else:
        data = input("Link or text: ").strip()
        name = safe_name(data.replace("https://", "").replace("http://", ""))
    if not data:
        print("Nothing to encode.")
        return pause()
    OUT.mkdir(exist_ok=True)
    path = OUT / f"{name}.png"
    img = qrcode.make(data)
    img.save(path)
    print(f"\nSaved: {path.resolve()}")
    print("Test it with your phone camera before you print or share it.")
    pause()


if __name__ == "__main__":
    main()
