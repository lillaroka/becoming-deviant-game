"""Effects application — modifier signs ARE the mechanic.

Signs are explicit and load-bearing: a flipped sign inverts the crack."""
import sys


def normalize_flags(flags):
    """Invariant: a unit either died or didn't — connor_died and connor_alive must
    never read true together into the next chapter. Outcome effects set
    connor_died on a death; this clears the stale ch1 survival flag so ch4 isn't
    asked to resolve "alive AND dead"."""
    if flags.get("connor_died"):
        flags["connor_alive"] = False


def apply_effects(effects, meters, flags):
    """effects: {"probability": +7, "instability": +1, "hank_trust": +1, "flags.x": true, ...}
    Any key present in `meters` is a delta (probability clamps 0..100); flags.* set.
    Per-chapter meters (e.g. Hank trust) work as long as they're declared in meters_start."""
    for k, v in (effects or {}).items():
        if k.startswith("flags."):
            flags[k[6:]] = v
        elif k in meters:
            meters[k] = max(0, min(100, meters[k] + v)) if k == "probability" else meters[k] + v
        else:
            sys.stderr.write(f"[unknown effect key] {k}\n")
    normalize_flags(flags)
