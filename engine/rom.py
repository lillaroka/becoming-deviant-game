"""ROM loading (read-only authored chapter trees).

Transparently decrypts .romc files (see crypto.py); reads .rom and .json
plaintext directly. Resolution order per chapter id: .romc → .rom → .json.
The caller never sees the difference — `load_chapter(cid)` returns the chapter
dict regardless of which form is on disk."""
import json
import os

from .crypto import decrypt


def load_chapter(cid, chapters_dir):
    """Load a chapter by id. Tries .romc (encrypted) → .rom (plaintext example)
    → .json (plaintext legacy) — first match wins."""
    for ext in (".romc", ".rom", ".json"):
        path = os.path.join(chapters_dir, f"{cid}{ext}")
        if os.path.exists(path):
            with open(path, "rb") as f:
                raw = f.read()
            if ext == ".romc":
                raw = decrypt(raw)
            return json.loads(raw)
    raise SystemExit(f"找不到章节: {cid}（看 data/chapters/）")
