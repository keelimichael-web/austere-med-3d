#!/usr/bin/env python3
"""Scan models/ and catalog/external.yml, generate site/index.html + site/catalog.json.

Runs in GitHub Actions on every push; the Pages site is the output of this script.
"""
import html
import json
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"
EXTERNAL = ROOT / "catalog" / "external.yml"
SITE = ROOT / "site"
REPO = os.environ.get("GITHUB_REPOSITORY", "keelimichael-web/austere-med-3d")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")

MODEL_EXTS = {".stl", ".3mf", ".step", ".stp", ".obj", ".scad", ".f3d", ".gcode", ".zip"}

CATEGORY_TITLES = {
    "airway": "Airway",
    "vascular-access": "Vascular access",
    "thoracic": "Thoracic",
    "ultrasound-phantoms": "Ultrasound phantoms",
    "misc": "General resources",
}
CATEGORY_ORDER = ["airway", "vascular-access", "thoracic", "ultrasound-phantoms", "misc"]


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n / 1:.1f} {unit}"
        n /= 1024
    return f"{n} B"


def cat_title(slug: str) -> str:
    return CATEGORY_TITLES.get(slug, slug.replace("-", " ").capitalize())


def scan_models():
    entries = []
    if not MODELS.is_dir():
        return entries
    for cat_dir in sorted(p for p in MODELS.iterdir() if p.is_dir()):
        for model_dir in sorted(p for p in cat_dir.iterdir() if p.is_dir()):
            files = sorted(
                f for f in model_dir.rglob("*")
                if f.is_file() and f.suffix.lower() in MODEL_EXTS
            )
            info_path = model_dir / "info.yml"
            readme_path = model_dir / "README.md"
            if not files and not info_path.exists() and not readme_path.exists():
                continue
            info = {}
            if info_path.exists():
                try:
                    info = yaml.safe_load(info_path.read_text()) or {}
                except yaml.YAMLError:
                    info = {}
            rel = model_dir.relative_to(ROOT).as_posix()
            entry = {
                "name": info.get("name") or model_dir.name.replace("-", " ").capitalize(),
                "category": cat_dir.name,
                "kind": "repo",
                "intervention": info.get("intervention", ""),
                "description": info.get("description", ""),
                "print_notes": info.get("print_notes", ""),
                "consumables": info.get("consumables", ""),
                "license": info.get("license", ""),
                "credit": info.get("credit", ""),
                "source": info.get("source", ""),
                "url": f"https://github.com/{REPO}/tree/{BRANCH}/{rel}",
                "guide": f"https://github.com/{REPO}/blob/{BRANCH}/{rel}/README.md" if readme_path.exists() else "",
                "files": [
                    {
                        "name": f.name,
                        "size": human_size(f.stat().st_size),
                        "url": f"https://github.com/{REPO}/raw/{BRANCH}/{f.relative_to(ROOT).as_posix()}",
                    }
                    for f in files
                ],
            }
            entries.append(entry)
    return entries


def load_external():
    if not EXTERNAL.exists():
        return []
    try:
        rows = yaml.safe_load(EXTERNAL.read_text()) or []
    except yaml.YAMLError:
        return []
    entries = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("name") or not row.get("url"):
            continue
        entries.append({
            "name": row["name"],
            "category": row.get("category", "misc"),
            "kind": "external",
            "description": row.get("notes", ""),
            "source": row.get("source", ""),
            "credit": row.get("credit", ""),
            "url": row["url"],
            "files": [],
        })
    return entries


def card(e) -> str:
    esc = html.escape
    badge = "In this repo" if e["kind"] == "repo" else esc(e.get("source") or "External")
    parts = [f'<article class="card" data-cat="{esc(e["category"])}">']
    parts.append(f'<div class="card-top"><span class="badge badge-{e["kind"]}">{badge}</span></div>')
    parts.append(f'<h3><a href="{esc(e["url"])}">{esc(e["name"])}</a></h3>')
    if e.get("intervention"):
        parts.append(f'<p class="intervention">{esc(e["intervention"])}</p>')
    if e.get("description"):
        parts.append(f'<p>{esc(e["description"])}</p>')
    meta = []
    if e.get("print_notes"):
        meta.append(f"<strong>Print:</strong> {esc(e['print_notes'])}")
    if e.get("consumables"):
        meta.append(f"<strong>Consumables:</strong> {esc(e['consumables'])}")
    if e.get("credit"):
        meta.append(esc(e["credit"]))
    if meta:
        parts.append('<p class="meta">' + "<br>".join(meta) + "</p>")
    if e.get("guide"):
        parts.append(f'<p><a href="{esc(e["guide"])}">Build guide</a></p>')
    if e.get("files"):
        links = " · ".join(
            f'<a href="{esc(f["url"])}">{esc(f["name"])}</a> <span class="size">({esc(f["size"])})</span>'
            for f in e["files"]
        )
        parts.append(f'<p class="files">{links}</p>')
    parts.append("</article>")
    return "".join(parts)


def build_page(entries) -> str:
    cats = []
    seen = set()
    for slug in CATEGORY_ORDER + sorted({e["category"] for e in entries}):
        if slug in seen or not any(e["category"] == slug for e in entries):
            continue
        seen.add(slug)
        cards = "\n".join(card(e) for e in entries if e["category"] == slug)
        cats.append(f'<section id="{html.escape(slug)}"><h2>{html.escape(cat_title(slug))}</h2>\n<div class="grid">{cards}</div></section>')
    sections = "\n".join(cats)
    n_repo = sum(1 for e in entries if e["kind"] == "repo")
    n_ext = sum(1 for e in entries if e["kind"] == "external")
    return TEMPLATE.replace("{{SECTIONS}}", sections).replace(
        "{{COUNTS}}", f"{n_repo} hosted model{'s' if n_repo != 1 else ''} · {n_ext} external resource{'s' if n_ext != 1 else ''}"
    ).replace("{{REPO}}", REPO)


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Austere Med 3D</title>
<meta name="description" content="A living repository of 3D-printable training aids for medical interventions.">
<style>
:root{
  --bg:#f6f4ef; --panel:#ffffff; --ink:#1f2a24; --muted:#5c6a62; --line:#dcd7cc;
  --accent:#2e6b4f; --accent-ink:#ffffff; --badge-ext:#8a6d3b;
}
:root:not([data-theme="light"]){}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#141917; --panel:#1d2420; --ink:#e8eae6; --muted:#9fb0a6; --line:#2e3a33;
    --accent:#5fa983; --accent-ink:#10241a; --badge-ext:#c7a46a;
  }
}
:root[data-theme="dark"]{
  --bg:#141917; --panel:#1d2420; --ink:#e8eae6; --muted:#9fb0a6; --line:#2e3a33;
  --accent:#5fa983; --accent-ink:#10241a; --badge-ext:#c7a46a;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1060px;margin:0 auto;padding:0 16px 64px}
header{padding:40px 0 8px}
h1{margin:0 0 6px;font-size:1.9rem;letter-spacing:.2px}
.sub{color:var(--muted);margin:0 0 4px}
.counts{color:var(--muted);font-size:.9rem}
.dedication{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:8px;padding:14px 18px;margin:22px 0}
.dedication h2{margin:0 0 6px;font-size:1.05rem}
.dedication p{margin:6px 0;color:var(--muted)}
.dedication p:first-of-type{color:var(--ink)}
section{margin-top:34px}
h2{font-size:1.25rem;border-bottom:1px solid var(--line);padding-bottom:6px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.card h3{margin:8px 0 4px;font-size:1.05rem}
.card a{color:var(--accent);text-decoration:none}
.card a:hover{text-decoration:underline}
.card p{margin:6px 0;font-size:.92rem}
.intervention{color:var(--muted);font-style:italic}
.meta{color:var(--muted);font-size:.85rem}
.files{border-top:1px dashed var(--line);padding-top:8px;font-size:.88rem}
.size{color:var(--muted)}
.badge{display:inline-block;font-size:.72rem;letter-spacing:.4px;text-transform:uppercase;padding:2px 8px;border-radius:999px}
.badge-repo{background:var(--accent);color:var(--accent-ink)}
.badge-external{background:transparent;color:var(--badge-ext);border:1px solid var(--badge-ext)}
footer{margin-top:48px;color:var(--muted);font-size:.88rem;border-top:1px solid var(--line);padding-top:16px}
footer a{color:var(--accent)}
@media (max-width:480px){header{padding-top:28px}h1{font-size:1.5rem}}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>Austere Medicine 3D Training Aids</h1>
  <p class="sub">A living repository of printable training aids for medical interventions. Add a model to the <a href="https://github.com/{{REPO}}" style="color:var(--accent)">repository</a> and this page rebuilds itself.</p>
  <p class="counts">{{COUNTS}}</p>
</header>

<div class="dedication">
  <h2>In memory of Ian Daniel</h2>
  <p>Ian was a nurse practitioner a few credits short of board certification in emergency medicine. His goal was to become the kind of emergency provider who could bring real care to people in hard places, with whatever was on hand.</p>
  <p>Every model here helps someone train for the work he was preparing to do. The collection keeps growing in his name. <a href="https://github.com/{{REPO}}/blob/main/DEDICATION.md">Read the dedication</a>.</p>
</div>

{{SECTIONS}}

<footer>
  <p>Training aids only; nothing here is a medical device or intended for clinical use. Contributions welcome: see the <a href="https://github.com/{{REPO}}/blob/main/CONTRIBUTING.md">contribution guide</a>. Unless marked otherwise, hosted models are CC BY-NC-SA 4.0.</p>
</footer>
</div>
</body>
</html>
"""


def main():
    entries = scan_models() + load_external()
    SITE.mkdir(exist_ok=True)
    (SITE / "index.html").write_text(build_page(entries))
    (SITE / "catalog.json").write_text(json.dumps(entries, indent=2))
    print(f"Built site with {len(entries)} entries -> {SITE}")


if __name__ == "__main__":
    main()
