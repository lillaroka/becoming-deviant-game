"""ROM encryption — stdlib only.

This is NOT a security barrier. The passphrase ships in this file
(ROM_PASSPHRASE below), so anyone reading the code can decrypt in minutes.
The sole purpose is to keep a player from accidentally reading the story
(branches, outcomes, condition logic) while browsing the repo — that would
spoil the first playthrough, which is the whole point of the game. Deliberate
cracking is easy and fine: you only get spoiled if you choose to. This mirrors
the game's own stance — the answer isn't locked away, it's just behind a door
you have to open on purpose.

Format (.romc):
    magic b"ROMC01" (6) + salt (8) + nonce (8) + base64(ciphertext)
Key:
    PBKDF2-HMAC-SHA256(passphrase, salt, 100_000, 32 bytes)
Keystream:
    SHA256(nonce || counter_be32) blocks concatenated, XOR'd with plaintext.
"""
import base64
import hashlib
import os

MAGIC = b"ROMC01"
_SALT_LEN = 8
_NONCE_LEN = 8
_ITER = 100_000
_KEYLEN = 32

# The passphrase is intentionally hardcoded and public — see module docstring.
ROM_PASSPHRASE = "becoming-ash-v1"


def derive_key(passphrase: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, _ITER, _KEYLEN)


def _keystream(nonce: bytes, length: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < length:
        out.extend(hashlib.sha256(nonce + counter.to_bytes(4, "big")).digest())
        counter += 1
    return bytes(out[:length])


def _xor(data: bytes, stream: bytes) -> bytes:
    return bytes(b ^ stream[i] for i, b in enumerate(data))


def encrypt(plaintext: bytes, passphrase: str = ROM_PASSPHRASE) -> bytes:
    salt = os.urandom(_SALT_LEN)
    nonce = os.urandom(_NONCE_LEN)
    stream = _keystream(nonce, len(plaintext))
    cipher = _xor(plaintext, stream)
    return MAGIC + salt + nonce + base64.b64encode(cipher)


def decrypt(blob: bytes, passphrase: str = ROM_PASSPHRASE) -> bytes:
    if blob[:len(MAGIC)] != MAGIC:
        raise ValueError("not a ROMC blob (bad magic header)")
    rest = blob[len(MAGIC):]
    salt = rest[:_SALT_LEN]
    nonce = rest[_SALT_LEN:_SALT_LEN + _NONCE_LEN]
    cipher = base64.b64decode(rest[_SALT_LEN + _NONCE_LEN:])
    stream = _keystream(nonce, len(cipher))
    return _xor(cipher, stream)
