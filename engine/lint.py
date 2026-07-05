"""No-free-lunch diagnostic + breath exemption.

A strategic choice 'has cost' if it has a breath/cost marker, a negative meter
effect, raises Instability (deepening the crack is the price of empathy), or the
chapter has tension (time). Breath actions are exempt."""


def choice_has_cost(ch, chapter_has_tension=False):
    if ch.get("breath") or ch.get("cost"):
        return True
    eff = ch.get("effects", {}) or {}
    for k, v in eff.items():
        if k.startswith("flags.") or not isinstance(v, (int, float)):
            continue
        if v < 0:
            return True
        if k == "instability" and v > 0:   # raising the crack-axis = a cost
            return True
    if chapter_has_tension:
        return True   # time costs every non-breath action
    has_upside = any((not k.startswith("flags.")) and isinstance(v, (int, float)) and v > 0
                     for k, v in eff.items())
    return not has_upside   # no upside → not a free lunch


def cmd_lint(engine, args):
    """No-free-lunch report: strategic choices with upside but no cost. Breath exempt."""
    chapter_id = args[0] if args else None
    if chapter_id is None:
        st = engine.load_save()
        chapter_id = st["chapter"] if st else "the-hostage"
    chapter = engine.load_chapter(chapter_id)
    has_tension = bool(chapter.get("tension"))
    breaths = [ch.get("id", "?") for beat in chapter["beats"].values() for ch in beat.get("choices", []) if ch.get("breath")]
    offenders = [(bid, ch) for bid, beat in chapter["beats"].items() for ch in beat.get("choices", []) if not choice_has_cost(ch, has_tension)]
    print(f"〔lint · 无白午餐 · {chapter_id}〕")
    if offenders:
        print("有上行、却没代价的战略选择:")
        for bid, ch in offenders:
            print(f"  · {bid} 「{ch.get('label', '?')}」 effects={ch.get('effects')}")
    else:
        print("✓ 全部通过——每个战略选择都付了代价")
    print(f"喘息动作(豁免): {', '.join(breaths) if breaths else '(无)'}")
