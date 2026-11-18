#!/usr/bin/env python3
# ZERO Folder Size Report - find out what is eating your disk space. Only reads, never changes anything.
# Needs: nothing extra (Python 3 only)
import os
from pathlib import Path


def pause():
    try:
        input("\nPress Enter to close...")
    except EOFError:
        pass


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def scan(folder):
    """Return (sizes of each top-level item, list of (size, path) for every file)."""
    top, files = {}, []
    for entry in os.scandir(folder):
        try:
            if entry.is_symlink():
                continue
            if entry.is_file():
                size = entry.stat().st_size
                top[entry.name] = top.get(entry.name, 0) + size
                files.append((size, entry.path))
            elif entry.is_dir():
                total = 0
                for root, _dirs, names in os.walk(entry.path):
                    for n in names:
                        p = os.path.join(root, n)
                        try:
                            if os.path.islink(p):
                                continue
                            s = os.path.getsize(p)
                        except OSError:
                            continue
                        total += s
                        files.append((s, p))
                top[entry.name + "/"] = total
        except OSError:
            continue
    return top, files


def build_report(folder, top, files, how_many=20):
    total = sum(top.values())
    lines = [f"Folder: {folder}", f"Total: {human(total)}", "", "Biggest items directly inside:"]
    for name, size in sorted(top.items(), key=lambda kv: -kv[1])[:how_many]:
        lines.append(f"  {human(size):>10}  {name}")
    lines += ["", f"Biggest {how_many} files anywhere inside:"]
    for size, path in sorted(files, reverse=True)[:how_many]:
        lines.append(f"  {human(size):>10}  {path}")
    return "\n".join(lines)


def main():
    print("=== ZERO Folder Size Report ===")
    print("Shows which folders and files take the most space. It only reads, it never changes anything.\n")
    folder = input("Folder to check (drag it here or paste the path): ").strip().strip('"').strip("'")
    if not folder or not os.path.isdir(folder):
        print("That folder was not found.")
        return pause()
    print("Measuring... big folders can take a minute.")
    top, files = scan(folder)
    report = build_report(folder, top, files)
    print("\n" + report)
    Path("size-report.txt").write_text(report, encoding="utf-8")
    print("\nSaved a copy as size-report.txt next to this script.")
    pause()


if __name__ == "__main__":
    main()
