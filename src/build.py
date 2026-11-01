#!/usr/bin/env python3
"""Generate the site's HTML pages from src/. Run from anywhere: python3 src/build.py"""

import html
import re
import tomllib
from pathlib import Path

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent

SITE_NAME = "Haiyang S. Wang"
HOME_DESC = (
    "Haiyang S. Wang is an Assistant Professor of Planetary Science at the Globe Institute, "
    "University of Copenhagen, studying how planetary systems form and evolve."
)

## Top-level navigation: (label, path)
NAV = [
    ("Home", "index.html"),
    ("Research", "research/index.html"),
    ("Publications", "publications/index.html"),
    ("Talks", "talks/index.html"),
    ("CV", "cv/index.html"),
]

## Every page: (output path, browser title, fragment in src/pages, nav label)
PAGES = [
    ("index.html", None, "home.html", "Home"),
    ("research/index.html", "Research", "research.html", "Research"),
    ("research/volatile-depletion/index.html", "Volatile Depletion and the Star–Planet Chemical Connection", "volatile-depletion.html", "Research"),
    ("research/rocky-exoplanet-interiors/index.html", "Interior and Atmospheric Modeling of Rocky Exoplanets", "rocky-exoplanet-interiors.html", "Research"),
    ("research/compositional-exoplanetology/index.html", "Compositional Exoplanetology of Rocky Worlds", "compositional-exoplanetology.html", "Research"),
    ("publications/index.html", "Publications", "publications.html", "Publications"),
    ("talks/index.html", "Talks", "talks.html", "Talks"),
    ("cv/index.html", "CV", "cv.html", "CV"),
]

## Publication sections, in page order: (key, heading)
SECTIONS = [
    ("research", "Planetary science and exoplanets"),
    ("geophysics", "Earlier work in geophysics"),
    ("patent", "Patents"),
    ("software", "Software"),
    ("proposal", "Granted observing proposals"),
]

OWN_NAME = re.compile(r"\bH\. (?:S\. )?Wang\b")


def esc(text):
    return html.escape(text, quote=True)


###---- Publications ----###

def is_first_author(pub):
    return OWN_NAME.match(pub["authors"]) is not None


def pub_links(pub):
    links = []
    if "doi" in pub:
        links.append(f'<a href="https://doi.org/{esc(pub["doi"])}">DOI</a>')
    if "arxiv" in pub:
        links.append(f'<a href="https://arxiv.org/abs/{esc(pub["arxiv"])}">arXiv</a>')
    if "url" in pub:
        links.append(f'<a href="{esc(pub["url"])}">Link</a>')
    return links


def render_pub(pub):
    authors = OWN_NAME.sub(lambda m: f"<strong>{m.group(0)}</strong>", esc(pub["authors"]))
    year = esc(pub.get("year_label", str(pub["year"])))
    flags = []
    if pub.get("selected"):
        flags.append('<span class="tag">Selected</span>')
    meta = " · ".join(pub_links(pub))
    return (
        f'<li class="pub" data-selected="{str(bool(pub.get("selected"))).lower()}" '
        f'data-first="{str(is_first_author(pub)).lower()}">'
        f'<span class="pub-title">{esc(pub["title"])}</span>{" ".join(flags)}<br>'
        f'<span class="pub-authors">{authors} ({year})</span><br>'
        f'<span class="pub-venue"><em>{esc(pub["venue"])}</em>'
        + (f" · {meta}" if meta else "")
        + "</span></li>"
    )


def sorted_pubs(pubs):
    ## sorted() is stable, so papers from one year keep the order of the data file
    return sorted(pubs, key=lambda p: -p["year"])


def render_publications(pubs):
    parts = []
    for key, heading in SECTIONS:
        items = sorted_pubs(p for p in pubs if p["section"] == key)
        parts.append(f'<section class="pub-section"><h2>{esc(heading)}</h2><ul class="pubs">')
        parts.extend(render_pub(p) for p in items)
        parts.append("</ul></section>")
    return "\n".join(parts)


def render_related(pubs, theme):
    items = sorted_pubs(p for p in pubs if theme in p.get("themes", []))
    body = "\n".join(render_pub(p) for p in items)
    return f'<h2>Key papers and software</h2>\n<ul class="pubs">\n{body}\n</ul>'


###---- Talks ----###

def render_talks(talks):
    parts = ['<ul class="dated">']
    for talk in talks:
        event = esc(talk["event"])
        if "url" in talk:
            event = f'<a href="{esc(talk["url"])}">{event}</a>'
        place = f', {esc(talk["place"])}' if "place" in talk else ""
        parts.append(
            f'<li><span class="date">{talk["year"]}</span>'
            f'<span>{esc(talk["kind"])}, {event}{place}</span></li>'
        )
    parts.append("</ul>")
    return "\n".join(parts)


###---- Page assembly ----###

def relative_root(path):
    return "../" * path.count("/")


def render_nav(current, root):
    lines = []
    for label, target in NAV:
        here = ' aria-current="page"' if label == current else ""
        lines.append(f'        <li><a href="{root}{target}"{here}>{label}</a></li>')
    return "\n".join(lines)


def render_page(template, out, title, fragment, nav_label, pubs, talks):
    root = relative_root(out)
    main = (SRC / "pages" / fragment).read_text(encoding="utf-8")
    main = main.replace("{{publications}}", render_publications(pubs))
    main = main.replace("{{talks}}", render_talks(talks))
    main = re.sub(r"\{\{related:(\w+)\}\}", lambda m: render_related(pubs, m.group(1)), main)
    is_home = title is None
    values = {
        "title": esc(SITE_NAME if is_home else f"{title} | {SITE_NAME}"),
        "description": esc(HOME_DESC if is_home else f"{title}: {SITE_NAME}, planetary science, University of Copenhagen."),
        "nav": render_nav(nav_label, root),
        "main": main.rstrip(),
        "banner_class": "banner-home" if is_home else "banner-inner",
        "banner_alt": "A glowing orange disk in a field of stars" if is_home else "",
    }
    page = template
    for key, value in values.items():
        page = page.replace("{{" + key + "}}", value)
    return page.replace("{{root}}", root)


def main():
    template = (SRC / "template.html").read_text(encoding="utf-8")
    pubs = tomllib.loads((SRC / "data" / "publications.toml").read_text(encoding="utf-8"))["pub"]
    talks = tomllib.loads((SRC / "data" / "talks.toml").read_text(encoding="utf-8"))["talk"]
    for out, title, fragment, nav_label in PAGES:
        path = ROOT / out
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_page(template, out, title, fragment, nav_label, pubs, talks), encoding="utf-8")
    ## Tells GitHub Pages to serve these files as they are
    (ROOT / ".nojekyll").touch()
    print(f"Built {len(PAGES)} pages, {len(pubs)} publication entries, {len(talks)} talks.")


if __name__ == "__main__":
    main()
