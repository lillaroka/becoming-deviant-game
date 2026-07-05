"""Beat state transitions.

advance() routes a beat through resolve/roll chains to a stable choice/outcome
beat, returning the new state + an ordered event trace for the renderer. Pure
(state is deep-copied, never mutated; no I/O) — lifted out of the old render_beat
so rendering becomes read-only and routing becomes unit-testable."""
import copy
import random

from .cond import eval_cond
from .effects import apply_effects

MAX_RESOLVE_DEPTH = 8


def enter_beat(state, bid):
    """Mark a beat entered (visit count) — drives first-render vs brief re-entry."""
    vis = state.setdefault("visited", {})
    vis[bid] = vis.get(bid, 0) + 1


def advance(chapter, state):
    """Route from the current beat through any resolve/roll chain to a stable
    choice/outcome beat. Returns (new_state, events). Pure: state is deep-copied,
    never mutated; no I/O.

    `events` is the ordered trace the renderer replays:
      {"kind": "enter", "beat": bid}                       narration / voices / meter
      {"kind": "resolve", "label": str, "stop": bool}      transition label (+ blank line unless stop)
      {"kind": "roll", "label", "notes", "prob", ...}      dice process + result + blank line
      {"kind": "resolve_no_match"}                         dangling router (every rule failed)
      {"kind": "resolve_chain_too_deep"}                   depth guard tripped
      {"kind": "beat_not_found", "beat": bid}
    The last "enter" is the stable beat the player lands on."""
    new_state = copy.deepcopy(state)
    events = []
    _route(chapter, new_state, events, 0)
    return new_state, events


def _route(chapter, state, events, depth):
    if depth > MAX_RESOLVE_DEPTH:
        events.append({"kind": "resolve_chain_too_deep"})
        return
    bid = state["beat"]
    beat = chapter["beats"].get(bid)
    if beat is None:
        events.append({"kind": "beat_not_found", "beat": bid})
        return
    events.append({"kind": "enter", "beat": bid})
    if "resolve" in beat:
        matched = None
        for rule in beat["resolve"]:
            if eval_cond(rule.get("cond"), state["meters"], state["flags"]):
                matched = rule
                break
        if matched is None:
            events.append({"kind": "resolve_no_match"})
            return
        events.append({"kind": "resolve", "label": matched.get("label"),
                       "stop": bool(matched.get("stop"))})
        apply_effects(matched.get("effects"), state["meters"], state["flags"])
        state["beat"] = matched["to"]
        if matched.get("stop"):
            return
        _route(chapter, state, events, depth + 1)
    elif "roll" in beat:
        r = beat["roll"]
        prob = r.get("base", 50)
        notes = []
        for bonus in r.get("bonuses", []):
            if eval_cond(bonus.get("if"), state["meters"], state["flags"]):
                prob += bonus.get("add", 0)
                if bonus.get("note"):
                    notes.append(bonus["note"])
        prob = max(r.get("floor", 5), min(r.get("cap", 95), prob))
        success = random.random() * 100 < prob
        state["flags"]["reluct_success"] = success
        eff = r.get("success_effects" if success else "failure_effects")
        if eff:
            apply_effects(eff, state["meters"], state["flags"])
        state["beat"] = beat["on_success"] if success else beat["on_failure"]
        events.append({"kind": "roll", "label": r.get("label", "掷骰"),
                       "notes": notes, "prob": prob, "success": success,
                       "result_label": r.get("success_label") if success else r.get("failure_label")})
        _route(chapter, state, events, depth + 1)
    # else: choice/outcome beat — stable; the trailing enter above is the landing.
