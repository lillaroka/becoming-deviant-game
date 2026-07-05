# Example: The Door

A tiny self-contained chapter (~50 lines of JSON) showing every ROM mechanic —
no Detroit spoilers. `chapters/door.rom` is plaintext on purpose: read it to
learn the format.

## What it demonstrates

- `meters_start` + `extra_meters` — the three core meters (Probability /
  Instability / Approach) plus a per-chapter extra (`trust`)
- `narration` — plain strings, plus conditional fragments `{"text": ..., "cond": ...}`
- `voices` — inner-voice lines gated by `cond` (which inner voice speaks depends on state)
- `choices` — `label` / `say` / `effects` / `to` / `cond` / `breath`
- `resolve` — deterministic threshold routing: the first rule whose `cond`
  holds fires automatically (meters/flags decide, not the player). This is the
  engine's no-dice heart.
- `outcome` — chapter ending
- `breath` — a low-cost "breathe" action (listen / coin / look away), exempt
  from the no-free-lunch check

## Run it

The engine reads `data/chapters/`. To play this example, copy it in:

```sh
cp examples/first-room/chapters/door.rom data/chapters/door.rom
python3 engine/room.py start door
```

## The format in one breath

A chapter is a JSON object: metadata (`id`, `title`, `start`, `meters_start`,
`extra_meters`, optional `tension`) + a `beats` map. Each beat is a scene:
`narration` to show, `voices` to whisper, `choices` to offer (each gated by
`cond`), and optionally a `resolve` list that auto-routes based on meters/flags.
Effects are explicit deltas (`"instability": +1`); the sign IS the mechanic —
flip it and you flip the meaning.
