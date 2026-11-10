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
WANTED = ROOT / "catalog" / "wanted.yml"
SITE = ROOT / "site"
REPO = os.environ.get("GITHUB_REPOSITORY", "keelimichael-web/resistance-medicine-printworks")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
PAGES_URL = f"https://{REPO.split('/')[0]}.github.io/{REPO.split('/')[1]}/"

MODEL_EXTS = {".stl", ".3mf", ".step", ".stp", ".obj", ".scad", ".f3d", ".gcode", ".zip", ".pdf"}

CATEGORY_TITLES = {
    "airway": "Airway",
    "vascular-access": "Vascular access",
    "thoracic": "Thoracic",
    "hemorrhage-wound-care": "Hemorrhage & wound care",
    "ultrasound-phantoms": "Ultrasound phantoms",
    "head-spine": "Head & spine",
    "misc": "General resources",
}
CATEGORY_ORDER = [
    "airway", "vascular-access", "thoracic",
    "hemorrhage-wound-care", "ultrasound-phantoms", "head-spine", "misc",
]

# Cross of Lorraine, the resistance symbol on the Annex cover
FAVICON = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
    "%3Crect width='32' height='32' rx='6' fill='%231a1d16'/%3E"
    "%3Cpath d='M14.5 4h3v5h6v3h-6v4h8v3h-8v9h-3v-9H6.5v-3h8v-4h-6V9h6z' fill='%23c1272d'/%3E%3C/svg%3E"
)

LORRAINE = (
    '<svg class="mark" viewBox="0 0 32 32" aria-hidden="true">'
    '<path d="M14.5 2h3v6h6v3h-6v4h9v3h-9v12h-3V18h-9v-3h9v-4h-6V8h6z" fill="currentColor"/>'
    "</svg>"
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
                "tier": info.get("tier", ""),
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
            "img": row.get("image", ""),
            "files": [],
        })
    return entries


# ---------- HTML ----------

STYLE = """
/* Field-manual theme drawn from the Annex cover: lantern-lit darks, olive
   drab, bone-paper text, Cross of Lorraine red as the single hot accent. */
:root{
  --bg:#15180f; --panel:#1e2316; --panel2:#242a1b; --ink:#e8e3d0; --muted:#a5a287;
  --line:#3a4028; --accent:#c8766a; --red:#c1272d; --red-ink:#f3e9e4;
  --amber:#d9a441; --chip:#2a301d; --badge-ext:#c7a46a;
}
@media (prefers-color-scheme: light){
  :root:not([data-theme="dark"]){
    --bg:#ece5d2; --panel:#f5f0e2; --panel2:#ebe4cf; --ink:#262a1a; --muted:#6d6a52;
    --line:#cfc6a8; --accent:#8c2f27; --red:#a3261f; --red-ink:#f8f2ea;
    --amber:#8a6420; --chip:#e2dac2; --badge-ext:#8a6d3b;
  }
}
:root[data-theme="light"]{
  --bg:#ece5d2; --panel:#f5f0e2; --panel2:#ebe4cf; --ink:#262a1a; --muted:#6d6a52;
  --line:#cfc6a8; --accent:#8c2f27; --red:#a3261f; --red-ink:#f8f2ea;
  --amber:#8a6420; --chip:#e2dac2; --badge-ext:#8a6d3b;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.58 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.disp{font-family:"Oswald","Arial Narrow",-apple-system,sans-serif;letter-spacing:.04em}
.wrap{max-width:1080px;margin:0 auto;padding:0 16px 64px}
header.site{padding:40px 0 4px;border-bottom:3px double var(--line);margin-bottom:6px}
.masthead{display:flex;align-items:flex-start;gap:16px}
.mark{width:44px;height:44px;flex:0 0 44px;color:var(--red);margin-top:4px}
h1{margin:0;font-family:"Oswald","Arial Narrow",sans-serif;font-weight:600;font-size:2.15rem;
   letter-spacing:.06em;text-transform:uppercase;line-height:1.15}
.kicker{font-family:"Oswald","Arial Narrow",sans-serif;font-size:.8rem;letter-spacing:.32em;
   text-transform:uppercase;color:var(--amber);margin:0 0 6px}
.sub{color:var(--muted);margin:10px 0 4px;max-width:74ch}
.sub a,.counts a{color:var(--accent)}
.sub em{color:var(--ink)}
.counts{color:var(--muted);font-size:.88rem;margin:4px 0 14px}
.epigraph{margin:14px 0 0;color:var(--muted);font-style:italic;font-size:1.02rem}
.epigraph b{color:var(--ink);font-weight:500}
.toolbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:14px 0 4px;position:sticky;top:0;
   background:var(--bg);padding:10px 0;z-index:5;border-bottom:1px solid var(--line)}
.search{flex:1 1 220px;min-width:180px;padding:9px 13px;border:1px solid var(--line);border-radius:4px;
   background:var(--panel);color:var(--ink);font-size:.95rem}
.search:focus{outline:2px solid var(--amber);border-color:transparent}
.pill{display:inline-block;padding:5px 12px;border-radius:3px;background:var(--chip);color:var(--ink);
   text-decoration:none;font-family:"Oswald","Arial Narrow",sans-serif;font-size:.78rem;
   letter-spacing:.14em;text-transform:uppercase;border:1px solid var(--line)}
.pill:hover{border-color:var(--amber);color:var(--amber)}
.dedication{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--red);
   padding:14px 18px;margin:20px 0}
.dedication h2{margin:0 0 6px;font-size:.95rem;border:none;padding:0;font-family:"Oswald","Arial Narrow",sans-serif;
   letter-spacing:.2em;text-transform:uppercase;color:var(--amber)}
.dedication p{margin:6px 0;color:var(--muted);font-size:.95rem}
.dedication p:first-of-type{color:var(--ink)}
.dedication a{color:var(--accent)}
section{margin-top:36px}
h2{font-family:"Oswald","Arial Narrow",sans-serif;font-weight:500;font-size:1.15rem;
   letter-spacing:.18em;text-transform:uppercase;border-bottom:1px solid var(--line);
   padding-bottom:7px;color:var(--ink)}
h2 .n{color:var(--red);margin-right:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:4px;padding:14px 16px;
   display:flex;flex-direction:column}
.thumb{width:calc(100% + 32px);margin:-14px -16px 12px;border-radius:3px 3px 0 0;display:block;
   border-bottom:2px solid var(--line)}
.card h3{margin:6px 0 2px;font-size:1.06rem;font-weight:600}
.card a{color:var(--accent);text-decoration:none}
.card a:hover{text-decoration:underline}
.card p{margin:6px 0;font-size:.92rem}
.intervention{color:var(--amber);font-size:.8rem;letter-spacing:.12em;text-transform:uppercase;
   font-family:"Oswald","Arial Narrow",sans-serif;margin-top:0}
.meta{color:var(--muted);font-size:.85rem}
.files{border-top:1px dashed var(--line);padding-top:8px;font-size:.88rem;margin-top:auto}
.size{color:var(--muted)}
.badge{display:inline-block;font-family:"Oswald","Arial Narrow",sans-serif;font-size:.68rem;
   letter-spacing:.18em;text-transform:uppercase;padding:2px 9px;border-radius:2px}
.badge-repo{background:var(--red);color:var(--red-ink)}
.badge-external{background:transparent;color:var(--badge-ext);border:1px solid var(--badge-ext)}
.btn{display:inline-block;margin:8px 8px 0 0;padding:7px 14px;border-radius:3px;background:var(--red);
   color:var(--red-ink);text-decoration:none;font-size:.85rem;font-family:"Oswald","Arial Narrow",sans-serif;
   letter-spacing:.1em;text-transform:uppercase}
.btn.ghost{background:transparent;color:var(--accent);border:1px solid var(--accent)}
footer{margin-top:52px;color:var(--muted);font-size:.88rem;border-top:3px double var(--line);padding-top:16px}
footer a{color:var(--accent)}
/* model detail pages */
.crumb{color:var(--muted);font-size:.9rem;margin:26px 0 0}
.crumb a{color:var(--accent);text-decoration:none}
article.model{background:var(--panel);border:1px solid var(--line);border-radius:4px;
   padding:10px 26px 22px;margin-top:14px}
article.model img{max-width:100%;border-radius:3px;border:1px solid var(--line)}
article.model h1{font-size:1.5rem;text-transform:none;letter-spacing:.02em}
article.model h2{font-size:1rem;border:none;margin-top:22px;padding:0}
article.model code{background:var(--chip);padding:1px 5px;border-radius:3px;font-size:.9em}
article.model a{color:var(--accent)}
.dl{background:var(--panel2);border:1px solid var(--line);border-radius:3px;padding:12px 16px;margin:14px 0}
.dl h2{margin:0 0 6px}
.dl ul{margin:4px 0;padding-left:20px}
.facts{color:var(--amber);font-size:.8rem;letter-spacing:.12em;text-transform:uppercase;
   font-family:"Oswald","Arial Narrow",sans-serif;margin:2px 0 10px}
@media (max-width:480px){header.site{padding-top:26px}h1{font-size:1.45rem}.mark{width:34px;height:34px;flex-basis:34px}}
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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600&display=swap" rel="stylesheet">
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
        parts.append(f'<a href="{esc(main_link)}"><img class="thumb" src="{esc(e["img"])}" alt="{esc(e["name"])} preview" loading="lazy" referrerpolicy="no-referrer"></a>')
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
    main_entries = [e for e in entries if e.get("tier") != "basic"]
    basic_entries = [e for e in entries if e.get("tier") == "basic"]
    cats, seen = [], set()
    for slug in CATEGORY_ORDER + sorted({e["category"] for e in main_entries}):
        if slug in seen or not any(e["category"] == slug for e in main_entries):
            continue
        seen.add(slug)
        cards = "\n".join(card(e) for e in main_entries if e["category"] == slug)
        cats.append(
            f'<section class="cat" id="{html.escape(slug)}">'
            f'<h2><span class="n">{len(seen):02d}</span>{html.escape(cat_title(slug))}</h2>\n'
            f'<div class="grid">{cards}</div></section>'
        )
    if basic_entries:
        cards = "\n".join(card(e) for e in basic_entries)
        cats.append(
            f'<section class="cat" id="workshop-basics">'
            f'<h2><span class="n">{len(seen) + 1:02d}</span>Workshop basics</h2>\n'
            '<p class="meta">Simple parametric originals built in this workshop before the '
            'curated collection above existed. They print and they work, but where a vetted '
            'community design above covers the same intervention, start there.</p>\n'
            f'<div class="grid">{cards}</div></section>'
        )
    wanted = yaml.safe_load(WANTED.read_text()) if WANTED.exists() else []
    if wanted:
        esc = html.escape
        items = "\n".join(
            f'<article class="card" data-search="{esc((w.get("name", "") + " wanted gap").lower())}">'
            f'<div><span class="badge badge-external">Wanted</span></div>'
            f'<h3>{esc(w.get("name", ""))}</h3>'
            f'<p>{esc(" ".join(str(w.get("notes", "")).split()))}</p>'
            f'<p class="meta">Swept {esc(str(w.get("swept", "")))} — nothing open exists yet.</p>'
            "</article>"
            for w in wanted
        )
        cats.append(
            f'<section class="cat" id="wanted">'
            f'<h2><span class="n">{len(seen) + (2 if basic_entries else 1):02d}</span>Wanted: designs that don&rsquo;t exist yet</h2>\n'
            '<p class="meta">Interventions with no open-source printable trainer anywhere, '
            'swept across MakerWorld, Printables, Thingiverse, NIH 3D, GrabCAD, Cults3D, and '
            'the open simulation literature. Design one and it has a home here.</p>\n'
            f'<div class="grid">{items}</div></section>'
        )
    pills = "".join(
        f'<a class="pill" href="#{html.escape(s)}">{html.escape(cat_title(s))}</a>'
        for s in CATEGORY_ORDER if s in seen
    )
    if basic_entries:
        pills += '<a class="pill" href="#workshop-basics">Workshop basics</a>'
    if wanted:
        pills += '<a class="pill" href="#wanted">Wanted</a>'
    n_repo = sum(1 for e in entries if e["kind"] == "repo")
    n_ext = sum(1 for e in entries if e["kind"] == "external")
    og_img = next((PAGES_URL + e["img"] for e in main_entries
                   if e.get("img") and e["kind"] == "repo"), "")
    out = head(
        "Resistance Medicine Printworks",
        "A living repository of 3D-printable training aids for medical interventions.",
        PAGES_URL, og_img,
    )
    out += f"""
<header class="site">
  <div class="masthead">
    {LORRAINE}
    <div>
      <p class="kicker">3D-printed training aids</p>
      <h1>Resistance Medicine<br>Printworks</h1>
    </div>
  </div>
  <p class="sub">A living repository of printable training aids for medical interventions, maintained by contributors to <em>Resistance Medicine: A Medical Annex to the Resistance Operating Concept</em>. Add a model to the <a href="https://github.com/{REPO}">repository</a> and this page rebuilds itself.</p>
  <p class="epigraph">&ldquo;<b>Medicine is resistance, and resistance is hope.</b>&rdquo; &mdash; from the Annex foreword</p>
  <p class="counts">{n_repo} hosted models · {n_ext} external resources · <a href="https://github.com/{REPO}/blob/main/CONTRIBUTING.md">how to contribute</a></p>
</header>

<div class="toolbar">
  <input class="search" id="q" type="search" placeholder="Search models: cric, IO, phantom, suture…" aria-label="Search models">
  {pills}
</div>

{chr(10).join(cats)}

<footer>
  <p>Training aids only; nothing here is a medical device or intended for clinical use. Contributions welcome: see the <a href="https://github.com/{REPO}/blob/main/CONTRIBUTING.md">contribution guide</a>. Unless marked otherwise, hosted models are CC BY-NC-SA 4.0.</p>
  <p id="cite"><strong>Cite as:</strong> <em>Resistance Medicine Printworks</em>, a living repository of 3D-printed medical training aids. {PAGES_URL}</p>
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
        f'{e["name"]} — Resistance Medicine Printworks',
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
  <p>Training aid only; not a medical device, not for clinical use. Part of <a href="../index.html">Resistance Medicine Printworks</a>.</p>
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
