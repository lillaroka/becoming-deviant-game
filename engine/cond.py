"""Condition evaluation — authored minimal DSL, restricted namespace.

Empty cond = True. Fail-open (True) + stderr warn — authoring should make this
rare, and a fail-open is logged, never silent."""
import sys


def eval_cond(expr, meters, flags):
    expr = (expr or "").strip()
    if not expr:
        return True
    ns = {"__builtins__": {},
          "flags": _FlagsProxy(flags),
          "meters": _MetersProxy(meters),
          "true": True, "false": False}
    try:
        return bool(eval(expr, ns))
    except Exception as e:
        sys.stderr.write(f"[cond fail-open] {expr!r}: {e}\n")
        return True


class _FlagsProxy:
    def __init__(self, d): self._d = d
    def __getitem__(self, k): return self._d.get(k, False)
    def get(self, k, default=False): return self._d.get(k, default)
    def __getattr__(self, k):
        if k.startswith("__"):
            raise AttributeError(k)        # don't shadow dunders
        return self[k]                      # flags.has_gun == flags["has_gun"]


class _MetersProxy:
    def __init__(self, d): self._d = d
    def __getitem__(self, k): return self._d.get(k, 0)
    def get(self, k, default=0): return self._d.get(k, default)
    def __getattr__(self, k):
        if k.startswith("__"):
            raise AttributeError(k)
        return self[k]                      # meters.instability == meters["instability"]
