"""Becoming Deviant — the room engine.

ROM  : data/chapters/*.json   (authored chapter trees, READ-ONLY)
SAVE : per-profile, e.g. data/ash.save.json   (read-write, JSON)

A "beat" = the scene the player is in + the choices visible there. Visibility
is condition-gated: a choice shows only if its `cond` holds against the current
meters + flags. This hides branches Ash hasn't earned — the reason an engine
exists, not a browser.

NO DICE — except one. The three meters (Probability / Instability / Approach)
move by authored effects; outcomes are deterministic, threshold-gated. The
engine's heart: Probability and Instability are anti-correlated by *authoring*
— you cannot optimize both. That tension IS the crack.
The one exception is the `roll` beat: a single, localized RNG exit, used only
where the theme needs an outcome that can't be gamed.

Usage:
    python3 engine/room.py start the-hostage
    python3 engine/room.py advance partners   # 带存档进下一章
    python3 engine/room.py replay partners    # 回本章开头(同携带),换条路走
    python3 engine/room.py beat
    python3 engine/room.py choose 2
    python3 engine/room.py status
    python3 engine/room.py where
    python3 engine/room.py reset
    python3 engine/room.py lint [chapter]
    python3 engine/room.py dump            # JSON 快照(给自动玩家/QA),只读不推进
"""
import json
import os
import sys

from .commands import (cmd_start, cmd_advance, cmd_replay, cmd_beat, cmd_choose,
                       cmd_status, cmd_where, cmd_reset)
from .dump import cmd_dump
from .lint import cmd_lint
from .rom import load_chapter
from .save import (load_save, write_save, fresh_save, carry_save,
                   checkpoint_path, write_checkpoint)

DEFAULT_PROFILE = "ash"

# 固定章序(Connor 线)——advance 用它校验防错序进章。replay/start 不受此限。
CHAPTER_ORDER = [
    "the-hostage", "partners", "the-interrogation", "waiting-for-hank",
    "the-nest", "russian-roulette", "the-eden-club", "the-bridge",
    "public-enemy", "meet-kamski", "last-chance-connor", "crossroads",
    "night-of-the-soul", "battle-for-detroit",
]

COMMANDS = {
    "start": cmd_start,
    "advance": cmd_advance,
    "replay": cmd_replay,
    "beat": cmd_beat,
    "choose": cmd_choose,
    "status": cmd_status,
    "where": cmd_where,
    "reset": cmd_reset,
    "lint": cmd_lint,
    "dump": cmd_dump,
}


def load_profile(name, profiles_dir, root):
    path = os.path.join(profiles_dir, f"{name}.json")
    if not os.path.exists(path):
        raise SystemExit(f"找不到 profile: {name}（看 profiles/）")
    with open(path, encoding="utf-8") as f:
        p = json.load(f)
    p.setdefault("id", name)
    p["save"] = os.path.join(root, p.get("save", f"data/{name}.save.json"))
    return p


def parse_cli(argv):
    profile = os.environ.get("DETROIT_PROFILE", DEFAULT_PROFILE)
    args = [a for a in argv[1:] if a != "--dev"]
    if args and args[0] in ("--profile", "-p"):
        if len(args) < 2:
            raise SystemExit("--profile 需要一个名字")
        profile, args = args[1], args[2:]
    elif args and args[0].startswith("--profile="):
        profile, args = args[0].split("=", 1)[1], args[1:]
    return profile, args


class Engine:
    """Holds all per-run state that used to be module-global (SAVE path,
    PROFILE_NAME, ROM/save roots). Handlers take `engine` and do I/O via it."""

    def __init__(self, profile_name, root):
        self.profile_name = profile_name
        self.root = root
        self.chapters_dir = os.path.join(root, "data", "chapters")
        self.profiles_dir = os.path.join(root, "profiles")
        self.profile = load_profile(profile_name, self.profiles_dir, root)
        self.save_path = self.profile["save"]
        self.chapter_order = CHAPTER_ORDER

    # ROM (read-only)
    def load_chapter(self, cid):
        return load_chapter(cid, self.chapters_dir)

    # SAVE (read-write)
    def load_save(self):
        return load_save(self.save_path)

    def write_save(self, state):
        write_save(self.save_path, state)

    def fresh_save(self, cid):
        return fresh_save(cid, self.profile_name, self.chapters_dir)

    def carry_save(self, prev, cid):
        return carry_save(prev, cid, self.profile_name, self.chapters_dir)

    def checkpoint_path(self, cid):
        return checkpoint_path(self.root, self.profile_name, cid)

    def write_checkpoint(self, state):
        write_checkpoint(self.root, self.profile_name, state)

    def run(self, argv):
        cmd = argv[0] if argv else "where"
        handler = COMMANDS.get(cmd)
        if handler is None:
            print(__doc__)
            return
        handler(self, argv[1:])


def main(argv=None):
    if argv is None:
        argv = sys.argv
    profile_name, args = parse_cli(argv)
    # engine/app.py → engine/ → project root
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    Engine(profile_name, root).run(args)
