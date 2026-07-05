"""Machine-readable beat snapshot — for automated players / QA.

Prints ONE JSON object: exactly what a human player sees on this beat
plus flags / fired / beat-id for diagnosis. Read-only — does NOT advance state.
Resolve-beats auto-route on entry (inside advance, called by start/choose), so
by the time you dump, `beat` is already past any router onto a stable beat."""
import json

from .render import (visible_choices, choice_used, meter_line,
                     narration_lines, voice_lines)


def cmd_dump(engine, args):
    state = engine.load_save()
    if state is None:
        print(json.dumps({"error": "no save", "hint": "start <chapter> first"}, ensure_ascii=False))
        return
    chapter = engine.load_chapter(state["chapter"])
    bid = state["beat"]
    beat = chapter["beats"].get(bid)
    if beat is None:
        print(json.dumps({"error": f"beat not found: {bid}", "chapter": state["chapter"]}, ensure_ascii=False))
        return
    opts = visible_choices(beat, state["meters"], state["flags"])
    choices = [{"n": i, "label": c.get("label", ""), "used": choice_used(c, state["fired"]), "id": c.get("id")}
               for i, c in enumerate(opts, 1)]
    snapshot = {
        "profile": engine.profile_name,
        "chapter": state["chapter"],
        "title": chapter.get("title", state["chapter"]),
        "beat": bid,
        "first_time": state.get("visited", {}).get(bid, 0) <= 1,
        "narration": narration_lines(chapter, state, bid),
        "voices": voice_lines(chapter, state, bid),
        "meter_line": meter_line(state["meters"], chapter.get("extra_meters"), state.get("tension", 0), (chapter.get("tension") or {}).get("per")),
        "meters": dict(state["meters"]),
        "choices": choices,
        "at_outcome": bool(beat.get("outcome")) and not opts,
        "outcome": beat.get("outcome"),
        "has_resolve_no_match": "resolve" in beat,
        "flags": dict(state["flags"]),
        "fired": list(state.get("fired", [])),
    }
    print(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")))
