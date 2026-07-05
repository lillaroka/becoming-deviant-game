"""Beat rendering — read-only. Replays the event trace from state.advance().

advance() decides routing (resolve/roll) and mutates state; render() only prints
what the player sees. No writes, no state mutation. The pure collectors
(narration_lines / voice_lines) are shared with dump."""
from .cond import eval_cond


def voice_label(ap):
    if ap <= -2: return "CyberLife 程序员"
    if ap >= 2:  return "萌芽异常"
    if ap > 0:   return "偏异常"
    if ap < 0:   return "偏程序"
    return "中立"


def meter_line(m, extra_labels=None, tension=None, tension_per=None):
    inst = m["instability"]
    bar = "◌" * min(int(inst / 5), 10) if inst > 0 else "·"
    s = f"〔概率 {m['probability']}% · 不稳定 {inst} {bar} · 声音: {voice_label(m['approach'])}"
    extra = extra_labels or {}
    for k in m:
        if k not in ("probability", "instability", "approach", "cyberlife_strikes") and k in extra:
            s += f" · {extra[k]} {m[k]:+d}"
    st = m.get("cyberlife_strikes", 0)
    if st > 0:
        s += f" · ⚠CyberLife {st}/3" + ("(下章回收)" if st >= 3 else "")
    if tension_per:
        s += f" · ⏱{tension_per - ((tension or 0) % tension_per)}"
    return s + "〕"


def choice_used(ch, fired):
    """A one-shot choice already taken (grey-out). Slot kept, number stable."""
    cid = ch.get("id") or ch.get("label")
    return bool(cid) and cid in fired and not ch.get("sticky")


def visible_choices(beat, meters, flags):
    out = []
    for ch in beat.get("choices", []):
        if not eval_cond(ch.get("cond"), meters, flags):
            continue
        out.append(ch)
    return out


def narration_lines(chapter, state, bid):
    """Pure: visible narration on this beat (first-time full vs re-entry brief)."""
    beat = chapter["beats"].get(bid, {})
    if state.get("visited", {}).get(bid, 0) <= 1:
        out = []
        for item in beat.get("narration", []):
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict) and eval_cond(item.get("cond"), state["meters"], state["flags"]):
                out.append(item["text"])
        return out
    return list(beat.get("return", []))


def voice_lines(chapter, state, bid):
    """Pure: audible inner-voice lines on this beat (pooled voices rotate by visit)."""
    beat = chapter["beats"].get(bid, {})
    visited = state.get("visited", {})
    out = []
    for v in beat.get("voices", []):
        if eval_cond(v.get("cond"), state["meters"], state["flags"]):
            pool = v.get("texts")
            out.append(pool[(visited.get(bid, 1) - 1) % len(pool)] if pool else v.get("text", ""))
    return out


def _render_surface(chapter, state, bid):
    """narration + voices + meter line — printed on every beat the route passes through."""
    for line in narration_lines(chapter, state, bid):
        print(line)
    for line in voice_lines(chapter, state, bid):
        print(line)
    ct = chapter.get("tension") or {}
    print(meter_line(state["meters"], chapter.get("extra_meters"), state.get("tension", 0), ct.get("per")))


def _render_terminus(chapter, state, bid):
    """choices or outcome — only printed on the final (stable) beat."""
    beat = chapter["beats"].get(bid, {})
    opts = visible_choices(beat, state["meters"], state["flags"])
    if not opts:
        if beat.get("outcome"):
            print(f"\n— 结局:{beat['outcome']} —")
            print("（这章到这里。进下一章:advance <chapter>——带 Instability / 声音 / 故事 flag。start = 重玩清零。）")
        else:
            print("\n（这条路到这里。）")
        return
    print("—— 我可以 ——")
    for i, ch in enumerate(opts, 1):
        if choice_used(ch, state["fired"]):
            print(f"  {i}) {ch['label']}（已查看）")
        else:
            print(f"  {i}) {ch['label']}")


def render(chapter, state, events):
    """Render the routing trace from state.advance(). Read-only — no writes.
    Output order mirrors the old render_beat exactly."""
    last = len(events) - 1
    for i, ev in enumerate(events):
        kind = ev["kind"]
        if kind == "enter":
            _render_surface(chapter, state, ev["beat"])
            if i == last:
                _render_terminus(chapter, state, ev["beat"])
        elif kind == "resolve":
            if ev.get("label"):
                print(f"\n→ {ev['label']}")
            if not ev.get("stop"):
                print()
        elif kind == "roll":
            print(f"\n〔{ev['label']}〕")
            for n in ev["notes"]:
                print(f"  + {n}")
            print(f"  → {ev['prob']}% 它顶得住。")
            print(f"\n→ {ev['result_label']}")
            print()
        elif kind == "resolve_no_match":
            print("\n（没有 resolve 规则匹配——这条路悬空了。）")
        elif kind == "resolve_chain_too_deep":
            print("（resolve 链太深——检查章节,可能有循环。）")
        elif kind == "beat_not_found":
            print(f"(找不到 beat: {ev['beat']})")


def surface_delta(before, after, extra_labels=None):
    labels = {"probability": "概率", "instability": "不稳定", "approach": "声音"}
    labels.update(extra_labels or {})
    for k in after:
        d = after[k] - before.get(k, 0)
        if d:
            print(f"   {labels.get(k, k)} {'+' if d > 0 else ''}{d}")
