#!/usr/bin/env python3
"""Back-compat entry — delegates to the engine package.

Usage is unchanged: `python3 engine/room.py <command> ...`.
The engine now lives in the engine/ package (split into modules); this file
keeps every existing invocation (PLAYER_HOME, profiles, docs, muscle memory)
working. New code should prefer `python -m engine`.
"""
import os
import sys

# Make the project root importable so `from engine.app import main` resolves
# whether invoked as `python3 engine/room.py` or `python -m engine.room`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.app import main  # noqa: E402

if __name__ == "__main__":
    main(sys.argv)
