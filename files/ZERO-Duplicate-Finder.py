#!/usr/bin/env python3
# ZERO Duplicate File Finder - finds identical files in a folder. It never deletes anything.
# Needs: nothing extra (Python 3 only)
import hashlib
import os
import shutil
from collections import defaultdict
from pathlib import Path

MOVED_DIR = "duplicates-moved"


def pause():
    try:
        input("\nPress Enter to close...")
    except EOFError:
        pass


def sha256(path, chunk=1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def find_duplicates(folder):
    """Return a list of groups. Each group is a list of paths with exactly the same content."""
    by_size = defaultdict(list)
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d != MOVED_DIR]
        for name in files:
            p = Path(root) / name
            try:
                if p.is_symlink():
                    continue
                by_size[p.stat().st_size].append(p)
            except OSError:
                continue
    groups = []
    for size, paths in by_size.items():
        if size == 0 or len(paths) < 2:
            continue
        by_hash = defaultdict(list)
        for p in paths:
            try:
                by_hash[sha256(p)].append(p)
            except OSError:
                continue
        groups += [sorted(v) for v in by_hash.values() if len(v) > 1]
    return sorted(groups)


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def wasted_bytes(groups):
    return sum(p.stat().st_size * (len(g) - 1) for g in groups for p in g[:1])


def move_extras(groups, folder):
    """Keep the first file of each group, move the other copies into a 'duplicates-moved' folder."""
    dest = Path(folder) / MOVED_DIR
    dest.mkdir(exist_ok=True)
    moved = 0
    for g in groups:
        for p in g[1:]:
            target = dest / p.name
            n = 1
            while target.exists():
                target = dest / f"{p.stem}_{n}{p.suffix}"
                n += 1
            shutil.move(str(p), str(target))
            moved += 1
    return moved


def main():
    print("=== ZERO Duplicate File Finder ===")
    print("Finds files with exactly the same content. Nothing is deleted.\n")
    folder = input("Folder to check (drag it here or paste the path): ").strip().strip('"').strip("'")
    if not folder or not os.path.isdir(folder):
        print("That folder was not found.")
        return pause()
    print("Checking... this can take a while for big folders.")
    groups = find_duplicates(folder)
    if not groups:
        print("No duplicates found.")
        return pause()
    lines = []
    for i, g in enumerate(groups, 1):
        lines.append(f"Group {i} ({human(g[0].stat().st_size)} each):")
        lines += [f"  {p}" for p in g]
        lines.append("")
    lines.append(f"{len(groups)} groups, about {human(wasted_bytes(groups))} could be freed.")
    report = Path("duplicates-report.txt")
    report.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[-1:]))
    print(f"Full list saved to: {report.resolve()}")
    if input("\nMove the extra copies into a '%s' folder? (y/N): " % MOVED_DIR).strip().lower() == "y":
        print(f"Moved {move_extras(groups, folder)} files. Check them, then delete that folder yourself if you agree.")
    pause()


if __name__ == "__main__":
    main()
