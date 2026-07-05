"""SAVE — per-profile read-write state (JSON).

ROM : data/chapters/*.json   (READ-ONLY)
SAVE: data/<profile>.save.json + data/<profile>.checkpoints/<chapter>.json"""
import json
import os

from .effects import normalize_flags
from .rom import load_chapter


def load_save(save_path):
    if not os.path.exists(save_path):
        return None
    with open(save_path, encoding="utf-8") as f:
        return json.load(f)


def write_save(save_path, state):
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def checkpoint_path(root, profile_name, chapter_id):
    return os.path.join(root, "data", f"{profile_name}.checkpoints", f"{chapter_id}.json")


def write_checkpoint(root, profile_name, state):
    """Snapshot a chapter's carry-in START state when you advance into it, so `replay`
    can retry that chapter with the same carry — single save slot otherwise forces a
    full ch1→here replay just to try a different branch."""
    path = checkpoint_path(root, profile_name, state["chapter"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def fresh_save(chapter_id, profile_name, chapters_dir):
    ch = load_chapter(chapter_id, chapters_dir)
    ms = dict(ch.get("meters_start", {"probability": 0, "instability": 0, "approach": 0}))
    ms.setdefault("cyberlife_strikes", 0)   # 造物主记账:累积偏离,跨章 carry
    return {
        "profile": profile_name,
        "chapter": chapter_id,
        "protagonist": ch.get("protagonist", "connor"),
        "beat": ch.get("start", "start"),
        "meters": ms,
        "flags": {},
        "fired": [],            # choice ids taken (one-shot tracking)
        "path": [],             # [[beat_id, choice_n, label], ...]
        "visited": {},          # beat_id → visit count (首次渲染 vs 重入过场)
        "tension": 0,           # non-breath actions taken (时间压力)
    }


def carry_save(prev, chapter_id, profile_name, chapters_dir):
    """New-chapter save carrying Connor's inner state forward (cross-chapter carry).
    Carry: instability, approach (the spine), and hank_trust CLAMPED to ±1 (a bounded goodwill
    head start — warm history gives a small lead into the next chapter, never enough to auto-win;
    the clamp IS the balance lever). All three reset on connor_died (new unit → Hank meets a stranger).
    Carry: flags (story state — emma_saved / connor_alive / executed_daniel ...).
    Reset: probability + per-chapter meters (e.g. deviant_stress / 压力), fired, path, visited, tension.
    Per balance.md: Probability + the chapter's own meter reset; Instability/Approach/Hank-trust carry.

    NOTE: the strikes/recycled/just_died logic below is Detroit-specific (the
    "造物主记账" three-strike recycle mechanic). Kept here because this engine is
    Detroit's own — not a generic narrative engine."""
    ch = load_chapter(chapter_id, chapters_dir)
    ms = dict(ch.get("meters_start", {"probability": 0, "instability": 0, "approach": 0}))
    flags = dict(prev.get("flags", {}))
    normalize_flags(flags)
    pm = prev.get("meters", {})
    strikes = pm.get("cyberlife_strikes", 0)
    recycled_now = strikes >= 3      # 这次 advance 触发回收(偏离临界 3 次)——一次性
    recycled = recycled_now or bool(flags.get("recycled", False))   # 持久
    died = bool(flags.get("connor_died", False)) or recycled_now   # 一次性死亡信号
    flags["connor_died"] = False
    flags["just_died"] = died
    flags["recycled"] = recycled
    if died:
        flags["connor_alive"] = True
    if not died:
        ms["instability"] = pm.get("instability", 0)
        ms["approach"] = pm.get("approach", 0)
        if "hank_trust" in pm:                                   # clamp ±1: head start, not a pass
            ms["hank_trust"] = max(-1, min(1, pm.get("hank_trust", 0)))
    ms["cyberlife_strikes"] = 0 if recycled_now else strikes
    return {
        "profile": profile_name,
        "chapter": chapter_id,
        "protagonist": ch.get("protagonist", "connor"),
        "beat": ch.get("start", "start"),
        "meters": ms,
        "flags": flags,
        "fired": [],
        "path": [],
        "visited": {},
        "tension": 0,
        "carried_from": prev.get("chapter"),
        "carried_died": died,
        "carried_recycled": recycled_now,
    }
