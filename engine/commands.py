"""Command handlers — each takes (engine, args), all I/O via engine.

Rendering is split into advance() + render(): advance (pure) routes resolve/roll
chains and returns (new_state, events); render (read-only) replays the events.
Handlers write the routed state exactly once, after advance — no writes inside
the render path."""
import json
import os

from .effects import apply_effects, normalize_flags
from .render import (render, meter_line, surface_delta, visible_choices,
                     choice_used)
from .state import enter_beat, advance


def cmd_start(engine, args):
    chapter_id = args[0] if args else None
    if not chapter_id:
        print("用法:start <chapter>(如 start the-hostage)"); return
    state = engine.fresh_save(chapter_id)
    enter_beat(state, state["beat"])
    state["path"].append([state["beat"], 0, "(进入)"])
    chapter = engine.load_chapter(chapter_id)
    state, events = advance(chapter, state)
    engine.write_save(state)
    print(f"{state['protagonist'].title()} 推门进入《{chapter.get('title', chapter_id)}》。\n")
    render(chapter, state, events, engine.chapter_order)


def cmd_advance(engine, args):
    """Carry Connor's inner state + story flags into the next chapter.
    `start` = fresh/replay; `advance` = carry on. Must be at an outcome."""
    chapter_id = args[0] if args else None
    if not chapter_id:
        print("用法:advance <chapter>(如 advance partners)"); return
    prev = engine.load_save()
    if prev is None:
        print("没有上一章存档——先 `start <chapter>` 玩通一章,再 advance。"); return
    prev_chapter = engine.load_chapter(prev["chapter"])
    prev_beat = prev_chapter["beats"].get(prev["beat"])
    if not prev_beat or not prev_beat.get("outcome"):
        print(f"还没到《{prev_chapter.get('title', prev['chapter'])}》的结局——先玩完这一章,再 advance。")
        return
    # advance 只能进固定章序的"下一章"——防错序。replay/start 不受此限。
    cur = prev["chapter"]
    if cur in engine.chapter_order:
        idx = engine.chapter_order.index(cur)
        next_chapter = engine.chapter_order[idx + 1] if idx < len(engine.chapter_order) - 1 else None
    else:
        next_chapter = None
    if next_chapter is None or chapter_id != next_chapter:
        hint = f"下一章是《{next_chapter}》——advance {next_chapter}" if next_chapter else "（你在的章不在主序、或已是终章）"
        print(f"advance 顺序错了。你在《{cur}》,只能进下一章。\n  {hint}\n  想重试别的章:replay <chapter>;想跳章调试:start <chapter>(清零 carry)。")
        return
    state = engine.carry_save(prev, chapter_id)
    enter_beat(state, state["beat"])
    state["path"].append([state["beat"], 0, "(从上一章进入)"])
    chapter = engine.load_chapter(chapter_id)
    engine.write_checkpoint(state)        # snapshot the carry-in START state (pre-route)
    state, events = advance(chapter, state)
    engine.write_save(state)
    print(f"{state['protagonist'].title()} 从《{prev_chapter.get('title', prev['chapter'])}》进入《{chapter.get('title', chapter_id)}》。")
    if state.get("carried_recycled"):
        print("（上一台 Connor 被 CyberLife 回收(3/3 strikes)——新机上线:Instability / 声音 / Hank 关系 归零。故事 flag 留着。）")
    elif state.get("carried_died"):
        print("（上一章 Connor 死了——CyberLife 送来新机:Instability / 声音 / Hank 关系 归零。故事 flag 留着。）")
    else:
        m = state["meters"]
        carry = f"Instability {m.get('instability', 0)} · 声音 {m.get('approach', 0)}"
        if m.get("hank_trust", 0) != 0:
            carry += f" · Hank {m['hank_trust']:+d}"
        print(f"（带着走:{carry}。Probability 与本章新仪表(压力等)重置。）")
    carried = [k for k, v in state["flags"].items() if v]
    if carried:
        print(f"（故事 flag 留着:{', '.join(carried)}）")
    print()
    render(chapter, state, events, engine.chapter_order)


def cmd_replay(engine, args):
    """Retry a chapter with the same carry-in state as last time (no re-earning the carry)."""
    chapter_id = args[0] if args else None
    if not chapter_id:
        print("用法:replay <chapter>(如 replay the-interrogation)"); return
    path = engine.checkpoint_path(chapter_id)
    if not os.path.exists(path):
        print(f"没有《{chapter_id}》的 checkpoint——先 advance 进过这章,才能 replay。"); return
    with open(path, encoding="utf-8") as f:
        state = json.load(f)
    state["meters"].setdefault("cyberlife_strikes", 0)   # 旧 checkpoint 兼容
    chapter = engine.load_chapter(chapter_id)
    state, events = advance(chapter, state)
    engine.write_save(state)
    print(f"{state.get('protagonist', 'connor').title()} 回到《{chapter.get('title', chapter_id)}》开头(同一套携带状态,换条路走)。\n")
    render(chapter, state, events, engine.chapter_order)


def cmd_beat(engine, args):
    state = engine.load_save()
    if state is None:
        print("房间是空的。先: room.py start <chapter>"); return
    chapter = engine.load_chapter(state["chapter"])
    state, events = advance(chapter, state)
    engine.write_save(state)
    render(chapter, state, events, engine.chapter_order)


def cmd_choose(engine, args):
    n = int(args[0])
    state = engine.load_save()
    if state is None:
        print("房间是空的。先: room.py start <chapter>"); return
    chapter = engine.load_chapter(state["chapter"])
    beat = chapter["beats"].get(state["beat"])
    opts = visible_choices(beat, state["meters"], state["flags"])
    if n < 1 or n > len(opts):
        print(f"无效选项 (1..{len(opts)})"); return
    pick = opts[n - 1]
    if choice_used(pick, state["fired"]):
        print(f"（「{pick['label']}」查看过了。）")
        return
    before = dict(state["meters"])
    apply_effects(pick.get("effects"), state["meters"], state["flags"])
    cid = pick.get("id") or pick.get("label")
    if cid:
        state["fired"].append(cid)
    print(f"我说:{pick['label']}\n")
    say = pick.get("say")
    if say:
        for line in (say if isinstance(say, list) else [say]):
            print(line)
        print()
    surface_delta(before, state["meters"], chapter.get("extra_meters"))
    # strike 叙事化:偏离被造物主记账,不是失败提示
    ds = state["meters"].get("cyberlife_strikes", 0) - before.get("cyberlife_strikes", 0)
    if ds > 0:
        st = state["meters"]["cyberlife_strikes"]
        print(f"   〔某个地方,造物主记了你一笔。{st}/3 ——这不是失败,是你偏离的痕迹。〕")
    # tension: non-breath actions press time; every `per`, a drip cost
    ct = chapter.get("tension")
    if not pick.get("breath") and ct and ct.get("per"):
        state["tension"] = state.get("tension", 0) + 1
        if state["tension"] % ct["per"] == 0:
            bt = dict(state["meters"])
            apply_effects({k: v for k, v in ct.items() if k != "per"}, state["meters"], state["flags"])
            labels = {"probability": "概率", "instability": "不稳定", "approach": "声音"}
            labels.update(chapter.get("extra_meters") or {})
            for k in state["meters"]:
                d = state["meters"][k] - bt.get(k, 0)
                if d:
                    print(f"   时间·磨蹭 {labels.get(k, k)} {'+' if d > 0 else ''}{d}")
    dest = pick.get("to", state["beat"])
    state["beat"] = dest
    enter_beat(state, dest)
    state["path"].append([dest, n, pick["label"]])
    state, events = advance(chapter, state)
    engine.write_save(state)
    print()
    render(chapter, state, events, engine.chapter_order)


def cmd_status(engine, args):
    state = engine.load_save()
    if state is None:
        print("房间是空的。"); return
    chapter = engine.load_chapter(state["chapter"])
    ct = chapter.get("tension") or {}
    print(f"《{chapter.get('title', state['chapter'])}》  ·  {state.get('protagonist', 'connor').title()}")
    print(meter_line(state["meters"], chapter.get("extra_meters"), state.get("tension", 0), ct.get("per")))
    if ct.get("per"):
        labels = {"probability": "概率", "instability": "不稳定", "approach": "声音"}
        labels.update(chapter.get("extra_meters") or {})
        cost = "、".join(f"{labels.get(k, k)}{v:+d}" for k, v in ct.items() if k != "per")
        t = state.get("tension", 0)
        print(f"时间压力 ⏱:每 {ct['per']} 个非喘息动作扣 {cost}(tension {t} · 下次还 {ct['per'] - t % ct['per']} 步)")
    normalize_flags(state["flags"])
    on = [k for k, v in state["flags"].items() if v]
    print(f"flag 亮着 ({len(on)}): {', '.join(on) if on else '(无)'}")


def cmd_where(engine, args):
    state = engine.load_save()
    if state is None:
        print("房间是空的。"); return
    chapter = engine.load_chapter(state["chapter"])
    print(f"位置:《{chapter.get('title', state['chapter'])}》")
    for i, row in enumerate(state["path"][-8:], 1):
        print(f"  #{i} {row[2]}")


def cmd_reset(engine, args):
    if os.path.exists(engine.save_path):
        os.remove(engine.save_path)
    print("房间已清空。")
