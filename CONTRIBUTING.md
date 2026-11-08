# Contributing

## Folder layout

Each model lives in its own folder under a category:

```
models/
  airway/
    wearable-cric-trainer/
      body.stl
      cover.stl
      info.yml
  thoracic/
    rib-section-ncd/
      ribs.3mf
      info.yml
```

Current categories: `airway`, `vascular-access`, `thoracic`, `ultrasound-phantoms`, `misc`. New category folders are picked up automatically; name them lowercase with hyphens.

## info.yml

Optional, but it makes the catalog page far more useful:

```yaml
name: Wearable Cric Trainer
intervention: Surgical cricothyrotomy
description: Strap-on trainer worn on the forearm or neck. Pair with simulated trachea (corrugated tubing) and skin (duct tape or Press'n Seal layers).
author: Jane Doe
source: https://example.com/original-posting   # if remixed or mirrored from elsewhere
license: CC BY-NC-SA 4.0
print_notes: PLA, 0.2 mm layers, no supports.
consumables: Corrugated 15 mm tubing, duct tape, 550 cord.
```

All fields are optional. Missing `name` falls back to the folder name.

## Build guides without print files

Some of the best training aids are builds, not prints (gelatin ultrasound phantoms, for example). Add a folder with a `README.md` describing the build and an `info.yml`; print files can come later.

## External links

Models hosted elsewhere go in `catalog/external.yml`:

```yaml
- name: Rib section for needle decompression
  category: thoracic
  url: https://www.thingiverse.com/thing:4018084
  source: Thingiverse
  notes: Pair with pork ribs or foam backing for tactile feedback.
```

## Large files

GitHub blocks files over 100 MB and warns over 50 MB. Keep meshes decimated where you can; use Git LFS for anything big.

## Attribution

Only put names on models and guides with the author's OK. "Working group contribution" is always an acceptable credit.
