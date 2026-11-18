#!/usr/bin/env python3
# ZERO Bulk Renamer - rename lots of files at once, with a preview first and an undo.
# Needs: nothing extra (Python 3 only)
import json
import os
import re
from pathlib import Path

UNDO_FILE = "rename-undo.json"


def pause():
    try:
        input("\nPress Enter to close...")
    except EOFError:
        pass


def list_files(folder):
    return sorted(p for p in Path(folder).iterdir()
                  if p.is_file() and not p.name.startswith(".") and p.name != UNDO_FILE)


def new_name(p, mode, index, prefix="", find="", replace=""):
    if mode == "number":
        return f"{prefix}{index:03d}{p.suffix}"
    if mode == "replace":
        return p.name.replace(find, replace) if find else p.name
    if mode == "tidy":
        return re.sub(r"[ _]+", "-", p.stem.strip()).lower() + p.suffix.lower()
    return p.name


def plan_renames(files, mode, **opts):
    """Return a list of (old_path, new_path) that is safe to run: no clashes, no no-ops."""
    plan, taken = [], {p.name.lower() for p in files}
    for i, p in enumerate(files, 1):
        name = new_name(p, mode, i, **opts)
        if name == p.name or not name:
            continue
        if name.lower() in taken and name.lower() != p.name.lower():
            continue                      # something with that name exists already, skip it
        taken.discard(p.name.lower())
        taken.add(name.lower())
        plan.append((p, p.with_name(name)))
    return plan


def apply(plan, folder):
    done = []
    for old, new in plan:
        os.rename(old, new)
        done.append([str(old), str(new)])
    (Path(folder) / UNDO_FILE).write_text(json.dumps(done, indent=1), encoding="utf-8")
    return len(done)


def undo(folder):
    f = Path(folder) / UNDO_FILE
    if not f.exists():
        return 0
    n = 0
    for old, new in reversed(json.loads(f.read_text(encoding="utf-8"))):
        if os.path.exists(new) and not os.path.exists(old):
            os.rename(new, old)
            n += 1
    f.unlink()
    return n


def main():
    print("=== ZERO Bulk Renamer ===")
    print("Renames the files directly inside a folder. You see a preview before anything changes.\n")
    folder = input("Folder (drag it here or paste the path): ").strip().strip('"').strip("'")
    if not folder or not os.path.isdir(folder):
        print("That folder was not found.")
        return pause()
    print("1 = Number them (holiday-001.jpg ...)   2 = Find and replace in names")
    print("3 = Tidy up (lowercase, spaces become dashes)   U = Undo the last rename here")
    choice = input("Choose 1/2/3/U: ").strip().lower()
    if choice == "u":
        print(f"Restored {undo(folder)} files.")
        return pause()
    files = list_files(folder)
    if choice == "1":
        plan = plan_renames(files, "number", prefix=input("Name to start with, e.g. holiday-: ").strip())
    elif choice == "2":
        plan = plan_renames(files, "replace", find=input("Find: "), replace=input("Replace with: "))
    elif choice == "3":
        plan = plan_renames(files, "tidy")
    else:
        print("No valid choice.")
        return pause()
    if not plan:
        print("Nothing to rename.")
        return pause()
    print(f"\n{len(plan)} files would change. First few:")
    for old, new in plan[:10]:
        print(f"  {old.name}  ->  {new.name}")
    if input("\nGo ahead? (y/N): ").strip().lower() == "y":
        print(f"Renamed {apply(plan, folder)} files. Run this again and choose U to undo.")
    else:
        print("Cancelled. Nothing was changed.")
    pause()


if __name__ == "__main__":
    main()
