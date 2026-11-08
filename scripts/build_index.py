#!/usr/bin/env python3
"""Build the catalog site from models/ and catalog/external.yml.

Outputs site/: index.html, style.css, catalog.json, img/ thumbnails, and a
detail page per hosted model under m/ rendered from its README.md.
Runs in GitHub Actions on every push; the Pages site is this script's output.
"""
import html
import json
import os
import shutil
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"
EXTERNAL = ROOT / "catalog" / "external.yml"
SITE = ROOT / "site"
REPO = os.environ.get("GITHUB_REPOSITORY", "keelimichael-web/austere-med-3d")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
PAGES_URL = f"https://{REPO.split('/')[0]}.github.io/{REPO.split('/')[1]}/"

MODEL_EXTS = {".stl", ".3mf", ".step", ".stp", ".obj", ".scad", ".f3d", ".gcode", ".zip"}

CATEGORY_TITLES = {
    "airway": "Airway",
    "vascular-access": "Vascular access",
    "thoracic": "Thoracic",
    "hemorrhage-wound-care": "Hemorrhage & wound care",
    "ultrasound-phantoms": "Ultrasound phantoms",
    "misc": "General resources",
}
CATEGORY_ORDER = [
    "airway", "vascular-access", "thoracic",
    "hemorrhage-wound-care", "ultrasound-phantoms", "misc",
]

FAVICON = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
    "%3Crect width='32' height='32' rx='7' fill='%232e6b4f'/%3E"
    "%3Cpath d='M13 7h6v6h6v6h-6v6h-6v-6H7v-6h6z' fill='white'/%3E%3C/svg%3E"
)


def human_size(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
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
            slug = f"{cat_dir.name}--{model_dir.name}"
            preview = next(
                (model_dir / n for n in ("photo.jpg", "photo.png", "preview.png", "preview.jpg")
                 if (model_dir / n).exists()),
                None,
            )
            entries.append({
                "name": info.get("name") or model_dir.name.replace("-", " ").capitalize(),
                "slug": slug,
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
                "page": f"m/{slug}.html" if readme_path.exists() else "",
                "img": f"img/{slug}{preview.suffix}" if preview else "",
                "_img_src": str(preview) if preview else "",
                "_readme": str(readme_path) if readme_path.exists() else "",
                "files": [
                    {
                        "name": f.name,
                        "size": human_size(f.stat().st_size),
                        "url": f"https://github.com/{REPO}/raw/{BRANCH}/{f.relative_to(ROOT).as_posix()}",
                    }
                    for f in files
                ],
            })
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
            "page": "",
            "img": "",
            "files": [],
        })
    return entries


# ---------- HTML ----------

STYLE = """
:root{
  --bg:#f6f4ef; --panel:#ffffff; --ink:#1f2a24; --muted:#5c6a62; --line:#dcd7cc;
  --accent:#2e6b4f; --accent-ink:#ffffff; --badge-ext:#8a6d3b; --chip:#eceae3;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#141917; --panel:#1d2420; --ink:#e8eae6; --muted:#9fb0a6; --line:#2e3a33;
    --accent:#5fa983; --accent-ink:#10241a; --badge-ext:#c7a46a; --chip:#232d28;
  }
}
:root[data-theme="dark"]{
  --bg:#141917; --panel:#1d2420; --ink:#e8eae6; --muted:#9fb0a6; --line:#2e3a33;
  --accent:#5fa983; --accent-ink:#10241a; --badge-ext:#c7a46a; --chip:#232d28;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:0 16px 64px}
header.site{padding:38px 0 6px}
h1{margin:0 0 8px;font-size:1.95rem;letter-spacing:.2px}
.sub{color:var(--muted);margin:0 0 4px;max-width:70ch}
.sub a,.counts a{color:var(--accent)}
.counts{color:var(--muted);font-size:.9rem;margin:4px 0 0}
.toolbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:18px 0 4px;position:sticky;top:0;background:var(--bg);padding:10px 0;z-index:5}
.search{flex:1 1 220px;min-width:180px;padding:9px 13px;border:1px solid var(--line);border-radius:999px;background:var(--panel);color:var(--ink);font-size:.95rem}
.search:focus{outline:2px solid var(--accent);border-color:transparent}
.pill{display:inline-block;padding:6px 13px;border-radius:999px;background:var(--chip);color:var(--ink);text-decoration:none;font-size:.85rem;border:1px solid var(--line)}
.pill:hover{border-color:var(--accent)}
.dedication{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:8px;padding:14px 18px;margin:18px 0}
.dedication h2{margin:0 0 6px;font-size:1.05rem;border:none;padding:0}
.dedication p{margin:6px 0;color:var(--muted);font-size:.95rem}
.dedication p:first-of-type{color:var(--ink)}
.dedication a{color:var(--accent)}
section{margin-top:34px}
h2{font-size:1.3rem;border-bottom:1px solid var(--line);padding-bottom:6px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px;display:flex;flex-direction:column}
.thumb{width:calc(100% + 32px);margin:-14px -16px 12px;border-radius:11px 11px 0 0;display:block;border-bottom:1px solid var(--line)}
.card h3{margin:6px 0 2px;font-size:1.08rem}
.card a{color:var(--accent);text-decoration:none}
.card a:hover{text-decoration:underline}
.card p{margin:6px 0;font-size:.92rem}
.intervention{color:var(--muted);font-style:italic;margin-top:0}
.meta{color:var(--muted);font-size:.85rem}
.files{border-top:1px dashed var(--line);padding-top:8px;font-size:.88rem;margin-top:auto}
.size{color:var(--muted)}
.badge{display:inline-block;font-size:.72rem;letter-spacing:.4px;text-transform:uppercase;padding:2px 9px;border-radius:999px}
.badge-repo{background:var(--accent);color:var(--accent-ink)}
.badge-external{background:transparent;color:var(--badge-ext);border:1px solid var(--badge-ext)}
.btn{display:inline-block;margin:8px 8px 0 0;padding:7px 14px;border-radius:8px;background:var(--accent);color:var(--accent-ink);text-decoration:none;font-size:.88rem}
.btn.ghost{background:transparent;color:var(--accent);border:1px solid var(--accent)}
footer{margin-top:48px;color:var(--muted);font-size:.88rem;border-top:1px solid var(--line);padding-top:16px}
footer a{color:var(--accent)}
/* model detail pages */
.crumb{color:var(--muted);font-size:.9rem;margin:26px 0 0}
.crumb a{color:var(--accent);text-decoration:none}
article.model{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:10px 26px 22px;margin-top:14px}
article.model img{max-width:100%;border-radius:8px;border:1px solid var(--line)}
article.model h1{font-size:1.6rem}
article.model h2{font-size:1.15rem;border:none;margin-top:22px;padding:0}
article.model code{background:var(--chip);padding:1px 5px;border-radius:4px;font-size:.9em}
.dl{background:var(--chip);border-radius:8px;padding:12px 16px;margin:14px 0}
.dl h2{margin:0 0 6px;font-size:1rem}
.dl ul{margin:4px 0;padding-left:20px}
.facts{color:var(--muted);font-size:.9rem;margin:2px 0 10px}
@media (max-width:480px){header.site{padding-top:26px}h1{font-size:1.5rem}}
.hidden{display:none}
"""

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
{og_img}<link rel="icon" href="{favicon}">
<link rel="stylesheet" href="{css}">
</head>
<body>
<div class="wrap">
"""

SEARCH_JS = """
<script>
(function(){
  var box = document.getElementById('q');
  if (!box) return;
  box.addEventListener('input', function(){
    var q = box.value.trim().toLowerCase();
    document.querySelectorAll('.card').forEach(function(c){
      c.classList.toggle('hidden', q && c.dataset.search.indexOf(q) === -1);
    });
    document.querySelectorAll('section.cat').forEach(function(s){
      s.classList.toggle('hidden', !s.querySelector('.card:not(.hidden)'));
    });
  });
})();
</script>
"""


def head(title, desc, url, og_img="", css="style.css"):
    og = f'<meta property="og:image" content="{html.escape(og_img)}">\n' if og_img else ""
    return HEAD.format(
        title=html.escape(title), desc=html.escape(desc),
        url=html.escape(url), og_img=og, favicon=FAVICON, css=css,
    )


def card(e) -> str:
    esc = html.escape
    badge = "In this repo" if e["kind"] == "repo" else esc(e.get("source") or "External")
    main_link = e["page"] or e["url"]
    search_blob = esc(" ".join(
        str(e.get(k, "")) for k in ("name", "intervention", "description", "category", "credit")
    ).lower())
    parts = [f'<article class="card" data-search="{search_blob}">']
    if e.get("img"):
        parts.append(f'<a href="{esc(main_link)}"><img class="thumb" src="{esc(e["img"])}" alt="{esc(e["name"])} preview" loading="lazy"></a>')
    parts.append(f'<div><span class="badge badge-{e["kind"]}">{badge}</span></div>')
    parts.append(f'<h3><a href="{esc(main_link)}">{esc(e["name"])}</a></h3>')
    if e.get("intervention"):
        parts.append(f'<p class="intervention">{esc(e["intervention"])}</p>')
    if e.get("description"):
        parts.append(f'<p>{esc(e["description"])}</p>')
    meta = []
    if e.get("print_notes"):
        meta.append(f"<strong>Print:</strong> {esc(e['print_notes'])}")
    if e.get("credit"):
        meta.append(esc(e["credit"]))
    if meta:
        parts.append('<p class="meta">' + "<br>".join(meta) + "</p>")
    if e.get("files"):
        links = " · ".join(
            f'<a href="{esc(f["url"])}">{esc(f["name"])}</a> <span class="size">({esc(f["size"])})</span>'
            for f in e["files"]
        )
        parts.append(f'<p class="files">{links}</p>')
    parts.append("</article>")
    return "".join(parts)


def build_index(entries) -> str:
    cats, seen = [], set()
    for slug in CATEGORY_ORDER + sorted({e["category"] for e in entries}):
        if slug in seen or not any(e["category"] == slug for e in entries):
            continue
        seen.add(slug)
        cards = "\n".join(card(e) for e in entries if e["category"] == slug)
        cats.append(
            f'<section class="cat" id="{html.escape(slug)}">'
            f"<h2>{html.escape(cat_title(slug))}</h2>\n"
            f'<div class="grid">{cards}</div></section>'
        )
    pills = "".join(
        f'<a class="pill" href="#{html.escape(s)}">{html.escape(cat_title(s))}</a>'
        for s in CATEGORY_ORDER if s in seen
    )
    n_repo = sum(1 for e in entries if e["kind"] == "repo")
    n_ext = sum(1 for e in entries if e["kind"] == "external")
    og_img = next((PAGES_URL + e["img"] for e in entries if e.get("img")), "")
    out = head(
        "Austere Medicine 3D Training Aids",
        "A living repository of 3D-printable training aids for medical interventions.",
        PAGES_URL, og_img,
    )
    out += f"""
<header class="site">
  <h1>Austere Medicine 3D Training Aids</h1>
  <p class="sub">A living repository of printable training aids for medical interventions, maintained by contributors to the <em>Medical Annex to the Resistance Operating Concept</em>. Add a model to the <a href="https://github.com/{REPO}">repository</a> and this page rebuilds itself.</p>
  <p class="counts">{n_repo} hosted models · {n_ext} external resources · <a href="https://github.com/{REPO}/blob/main/CONTRIBUTING.md">how to contribute</a></p>
</header>

<div class="toolbar">
  <input class="search" id="q" type="search" placeholder="Search models: cric, IO, phantom, suture…" aria-label="Search models">
  {pills}
</div>

<div class="dedication">
  <h2>In memory of Ian Daniel</h2>
  <p>Ian was a nurse practitioner a few credits short of board certification in emergency medicine. His goal was to become the kind of emergency provider who could bring real care to people in hard places, with whatever was on hand.</p>
  <p>Every model here helps someone train for the work he was preparing to do. The collection keeps growing in his name. <a href="https://github.com/{REPO}/blob/main/DEDICATION.md">Read the dedication</a>.</p>
</div>

{chr(10).join(cats)}

<footer>
  <p>Training aids only; nothing here is a medical device or intended for clinical use. Contributions welcome: see the <a href="https://github.com/{REPO}/blob/main/CONTRIBUTING.md">contribution guide</a>. Unless marked otherwise, hosted models are CC BY-NC-SA 4.0.</p>
  <p id="cite"><strong>Cite as:</strong> <em>Austere Medicine 3D Training Aids</em>, living repository. {PAGES_URL}</p>
</footer>
</div>
{SEARCH_JS}
</body>
</html>
"""
    return out


def build_model_page(e) -> str:
    md_text = Path(e["_readme"]).read_text()
    lines = md_text.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    md_text = "\n".join(lines)
    for local in ("preview.png", "preview.jpg", "photo.jpg", "photo.png"):
        md_text = md_text.replace(f"]({local})", f"](../{e['img']})" if e.get("img") else f"]({local})")
    body = markdown.markdown(md_text, extensions=["fenced_code", "tables"])
    esc = html.escape
    facts = " · ".join(
        esc(e[k]) for k in ("intervention", "license", "credit") if e.get(k)
    )
    downloads = "".join(
        f'<li><a href="{esc(f["url"])}">{esc(f["name"])}</a> <span class="size">({esc(f["size"])})</span></li>'
        for f in e["files"]
    )
    out = head(
        f'{e["name"]} — Austere Med 3D',
        e.get("description") or e["name"],
        f'{PAGES_URL}m/{e["slug"]}.html',
        (PAGES_URL + e["img"]) if e.get("img") else "",
        css="../style.css",
    )
    out += f"""
<p class="crumb"><a href="../index.html">← All models</a> / {esc(cat_title(e["category"]))}</p>
<article class="model">
<h1>{esc(e["name"])}</h1>
<p class="facts">{facts}</p>
<div class="dl">
<h2>Download</h2>
<ul>{downloads}</ul>
<a class="btn ghost" href="{esc(e["url"])}">Source folder on GitHub</a>
</div>
{body}
</article>
<footer>
  <p>Training aid only; not a medical device, not for clinical use. Part of <a href="../index.html">Austere Medicine 3D Training Aids</a>.</p>
</footer>
</div>
</body>
</html>
"""
    return out


def main():
    entries = scan_models() + load_external()
    SITE.mkdir(exist_ok=True)
    (SITE / "img").mkdir(exist_ok=True)
    (SITE / "m").mkdir(exist_ok=True)
    (SITE / "style.css").write_text(STYLE)
    for e in entries:
        src = e.pop("_img_src", "")
        if src and e.get("img"):
            shutil.copyfile(src, SITE / e["img"])
    n_pages = 0
    for e in entries:
        readme = e.pop("_readme", "")
        if readme:
            e["_readme"] = readme
            (SITE / "m" / f'{e["slug"]}.html').write_text(build_model_page(e))
            e.pop("_readme")
            n_pages += 1
    (SITE / "index.html").write_text(build_index(entries))
    (SITE / "catalog.json").write_text(json.dumps(entries, indent=2))
    print(f"Built site: {len(entries)} entries, {n_pages} model pages -> {SITE}")


if __name__ == "__main__":
    main()
