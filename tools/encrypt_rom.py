#!/usr/bin/env python3
"""Encrypt a plaintext chapter ROM (.json) into a .romc file.

Authoring / publishing tool — NOT needed at runtime. Used when publishing the
public repo: takes the private repo's plaintext data/chapters/*.json and emits
encrypted data/chapters/*.romc so the story can ship without spoiling browsers.

Usage:
    python3 tools/encrypt_rom.py data/chapters/the-hostage.json
    python3 tools/encrypt_rom.py data/chapters/*.json        # batch
    python3 tools/encrypt_rom.py --all                       # every chapter
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.crypto import encrypt  # noqa: E402


def encrypt_one(json_path):
    with open(json_path, "rb") as f:
        plaintext = f.read()
    blob = encrypt(plaintext)
    out = json_path[:-5] + ".romc"   # .json → .romc
    with open(out, "wb") as f:
        f.write(blob)
    return out


def main(argv):
    args = argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return
    if args[0] == "--all":
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        args = sorted(glob.glob(os.path.join(root, "data", "chapters", "*.json")))
    for p in args:
        if not p.endswith(".json"):
            print(f"  跳过(非 .json): {p}")
            continue
        out = encrypt_one(p)
        print(f"  {os.path.basename(p)} → {os.path.basename(out)} ({os.path.getsize(out)} bytes)")


if __name__ == "__main__":
    main(sys.argv)
