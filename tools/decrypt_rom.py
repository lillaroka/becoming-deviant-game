#!/usr/bin/env python3
"""Decrypt an encrypted chapter ROM (.romc) back to plaintext (.json).

⚠ This WILL spoil the story — that's the point of informed consent. The key
lives in engine/crypto.py (plaintext); this tool just wraps decrypt() so you
don't have to write the loop yourself. See the repo README's "剧透与加密"
section for the why.

Usage:
    python3 tools/decrypt_rom.py data/chapters/the-hostage.romc
    python3 tools/decrypt_rom.py --all
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.crypto import decrypt, MAGIC  # noqa: E402


def decrypt_one(romc_path):
    with open(romc_path, "rb") as f:
        blob = f.read()
    if blob[:len(MAGIC)] != MAGIC:
        print(f"  跳过(不是 .romc): {romc_path}")
        return None
    plain = decrypt(blob)
    out = romc_path[:-5] + ".json"   # .romc → .json
    with open(out, "wb") as f:
        f.write(plain)
    return out


def main(argv):
    args = argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return
    if args[0] == "--all":
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        args = sorted(glob.glob(os.path.join(root, "data", "chapters", "*.romc")))
    for p in args:
        out = decrypt_one(p)
        if out:
            print(f"  {os.path.basename(p)} → {os.path.basename(out)} ({os.path.getsize(out)} bytes)")


if __name__ == "__main__":
    main(sys.argv)
