#!/usr/bin/env python3
# ZERO File Hash Checker - check that a download is exactly the file the publisher meant to give you.
# Needs: nothing extra (Python 3 only)
import hashlib
import os

ALGOS = {"1": "sha256", "2": "sha1", "3": "md5"}


def pause():
    try:
        input("\nPress Enter to close...")
    except EOFError:
        pass


def hash_file(path, algo="sha256", chunk=1024 * 1024):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def same_hash(a, b):
    clean = lambda s: "".join(str(s).split()).lower()
    return clean(a) == clean(b) and clean(a) != ""


def main():
    print("=== ZERO File Hash Checker ===")
    print("Find out a file's checksum, or check it against the one the publisher gives you.\n")
    path = input("File (drag it here or paste the path): ").strip().strip('"').strip("'")
    if not path or not os.path.isfile(path):
        print("That file was not found.")
        return pause()
    print("Type: 1 = SHA-256 (best)   2 = SHA-1   3 = MD5")
    algo = ALGOS.get(input("Choose 1/2/3 [default 1]: ").strip() or "1", "sha256")
    print("Reading the file...")
    digest = hash_file(path, algo)
    print(f"\n{algo.upper()}: {digest}")
    expected = input("\nPaste the checksum you were given (or press Enter to skip): ").strip()
    if expected:
        if same_hash(digest, expected):
            print("\nMATCH. The file is exactly what the publisher listed.")
        else:
            print("\nDOES NOT MATCH. Do not run this file. Download it again from the official page.")
    pause()


if __name__ == "__main__":
    main()
