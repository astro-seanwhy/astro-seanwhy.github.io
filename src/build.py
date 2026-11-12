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

## ID of the Contact form from the Formspree dashboard (the end of formspree.io/f/...).
## While empty, the form shows but cannot send.
FORMSPREE_ID = "xvkagrqa"

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
    ("research/volatile-depletion/index.html", "Star–planet chemical connection", "volatile-depletion.html", "Research"),
    ("research/rocky-exoplanet-interiors/index.html", "Rocky exoplanet interiors and atmospheres", "rocky-exoplanet-interiors.html", "Research"),
    ("research/habitability-origin-of-life/index.html", "Habitability and origin of life", "habitability-origin-of-life.html", "Research"),
    ("research/latest-results/index.html", "Latest results", "latest-results.html", "Research"),
    ("publications/index.html", "Publications", "publications.html", "Publications"),
    ("talks/index.html", "Talks", "talks.html", "Talks"),
    ("cv/index.html", "CV", "cv.html", "CV"),
]

## Pages laid out in a wider column, for cards and figures
WIDE = {"index.html", "research/index.html", "research/latest-results/index.html"}

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


def render_pub(pub, summary=False):
    authors = OWN_NAME.sub(lambda m: f"<strong>{m.group(0)}</strong>", esc(pub["authors"]))
    year = esc(pub.get("year_label", str(pub["year"])))
    meta = " · ".join(pub_links(pub))
    extra = f'<br><span class="pub-summary">{esc(pub["summary"])}</span>' if summary and "summary" in pub else ""
    return (
        f'<li class="pub" data-first="{str(is_first_author(pub)).lower()}">'
        f'<span class="pub-title">{esc(pub["title"])}</span><br>'
        f'<span class="pub-authors">{authors} ({year})</span><br>'
        f'<span class="pub-venue"><em>{esc(pub["venue"])}</em>'
        + (f" · {meta}" if meta else "")
        + f"</span>{extra}</li>"
    )


def sorted_pubs(pubs):
    ## sorted() is stable, so papers from one year keep the order of the data file
    return sorted(pubs, key=lambda p: -p["year"])


def theme_pubs(pubs, theme):
    if "section" in theme:
        return sorted_pubs(p for p in pubs if p["section"] == theme["section"])
    return sorted_pubs(p for p in pubs if theme["key"] in p.get("themes", []))


def render_publications(pubs, themes):
    ## Two views of the list; assets/site.js switches between them
    parts = ['<div class="pub-view" data-view="all">']
    for key, heading in SECTIONS:
        items = sorted_pubs(p for p in pubs if p["section"] == key)
        parts.append(f'<section class="pub-section"><h2>{esc(heading)}</h2><ul class="pubs">')
        parts.extend(render_pub(p) for p in items)
        parts.append("</ul></section>")
    parts.append('</div>\n<div class="pub-view" data-view="themes" hidden>')
    for theme in themes:
        heading = esc(theme["title"])
        if "page" in theme:
            heading = f'<a href="{{{{root}}}}{theme["page"]}">{heading}</a>'
        parts.append(f'<section class="pub-section"><h2>{heading}</h2><ul class="pubs">')
        parts.extend(render_pub(p) for p in theme_pubs(pubs, theme))
        parts.append("</ul></section>")
    parts.append("</div>")
    return "\n".join(parts)


def render_featured(pubs):
    parts = ['<ul class="pubs">']
    for pub in sorted_pubs(p for p in pubs if p.get("featured")):
        title = esc(pub["title"])
        if "doi" in pub:
            title = f'<a href="https://doi.org/{esc(pub["doi"])}">{title}</a>'
        parts.append(
            f'<li class="pub"><span class="pub-title">{title}</span><br>'
            f'<span class="pub-venue"><em>{esc(pub["venue"])}</em> ({pub["year"]})</span><br>'
            f'{esc(pub["summary"])}</li>'
        )
    parts.append("</ul>")
    return "\n".join(parts)


def render_latest(pubs, year):
    ## One block per research paper of the year, each with a figure from the paper
    parts = []
    for pub in pubs:
        if pub["section"] != "research" or pub["year"] != year:
            continue
        title = esc(pub["title"])
        if "doi" in pub:
            title = f'<a href="https://doi.org/{esc(pub["doi"])}">{title}</a>'
        elif "arxiv" in pub:
            title = f'<a href="https://arxiv.org/abs/{esc(pub["arxiv"])}">{title}</a>'
        authors = OWN_NAME.sub(lambda m: f"<strong>{m.group(0)}</strong>", esc(pub["authors"]))
        meta = " · ".join([f'<em>{esc(pub["venue"])}</em>'] + pub_links(pub))
        figure = ""
        if "figure" in pub:
            src = "{{root}}" + esc(pub["figure"])
            figure = (
                f'<figure class="result-fig"><a href="{src}"><img src="{src}" alt="{esc(pub["figure_alt"])}" loading="lazy"></a>'
                f'<figcaption>{esc(pub["figure_note"])}</figcaption></figure>'
            )
        parts.append(
            f'<article class="result">{figure}<div><h2>{title}</h2>'
            f'<p class="pub-authors">{authors}</p><p class="pub-venue">{meta}</p>'
            f'<p>{esc(pub.get("summary", ""))}</p></div></article>'
        )
    return "\n".join(parts)


###---- Research themes ----###

def find_theme(themes, key):
    for theme in themes:
        if theme["key"] == key:
            return theme
    raise KeyError(f"no theme named {key}")


def render_theme_cards(themes):
    ## The figure and the title of a card link to the theme's page
    parts = ['<div class="cards">']
    for theme in themes:
        if "page" not in theme:
            continue
        parts.append(
            f'<article class="card"><a class="card-link" href="{{{{root}}}}{theme["page"]}">'
            f'<img src="{{{{root}}}}{theme["image"]}" alt="{esc(theme["alt"])}">'
            f'<h3>{esc(theme["title"])}</h3></a>'
            f'<p class="card-sub">{esc(theme["subtitle"])}</p></article>'
        )
    parts.append("</div>")
    return "\n".join(parts)


def render_theme_head(theme):
    return (
        '<p class="crumb"><a href="../index.html">Research</a></p>\n'
        f'<h1>{esc(theme["title"])}</h1>\n<p class="subtitle">{esc(theme["subtitle"])}</p>'
    )


def render_theme_figure(theme):
    return f'<figure class="fig-theme"><img src="{{{{root}}}}{theme["image"]}" alt="{esc(theme["alt"])}"></figure>'


def render_related(pubs, theme):
    body = "\n".join(render_pub(p, summary=True) for p in theme_pubs(pubs, theme))
    return f'<h2>Publications</h2>\n<ul class="pubs">\n{body}\n</ul>'


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


###---- Contact form ----###

def form_values():
    if FORMSPREE_ID:
        return {
            "form_action": f' action="https://formspree.io/f/{esc(FORMSPREE_ID)}"',
            "form_disabled": "",
            "form_note": "",
        }
    return {
        "form_action": "",
        "form_disabled": " disabled",
        "form_note": "This form is not connected yet, so it cannot send messages.",
    }


###---- Page assembly ----###

def relative_root(path):
    return "../" * path.count("/")


def render_nav(current, root):
    lines = []
    for label, target in NAV:
        here = ' aria-current="page"' if label == current else ""
        lines.append(f'        <li><a href="{root}{target}"{here}>{label}</a></li>')
    return "\n".join(lines)


def include(match):
    ## {{include:name}} inserts src/partials/name.html or name.svg
    for suffix in (".html", ".svg"):
        path = SRC / "partials" / (match.group(1) + suffix)
        if path.exists():
            return path.read_text(encoding="utf-8").rstrip()
    raise FileNotFoundError(f"no partial named {match.group(1)}")


def render_page(template, out, title, fragment, nav_label, pubs, talks, themes):
    root = relative_root(out)
    main = (SRC / "pages" / fragment).read_text(encoding="utf-8")
    ## Twice, because a partial may include a figure
    for _ in range(2):
        main = re.sub(r"\{\{include:([\w-]+)\}\}", include, main)
    main = main.replace("{{featured}}", render_featured(pubs))
    main = main.replace("{{themes}}", render_theme_cards(themes))
    main = main.replace("{{publications}}", render_publications(pubs, themes))
    main = main.replace("{{talks}}", render_talks(talks))
    main = re.sub(r"\{\{latest:(\d+)\}\}", lambda m: render_latest(pubs, int(m.group(1))), main)
    main = re.sub(r"\{\{theme_head:([\w-]+)\}\}", lambda m: render_theme_head(find_theme(themes, m.group(1))), main)
    main = re.sub(r"\{\{theme_figure:([\w-]+)\}\}", lambda m: render_theme_figure(find_theme(themes, m.group(1))), main)
    main = re.sub(r"\{\{related:([\w-]+)\}\}", lambda m: render_related(pubs, find_theme(themes, m.group(1))), main)
    for key, value in form_values().items():
        main = main.replace("{{" + key + "}}", value)
    is_home = title is None
    values = {
        "title": esc(SITE_NAME if is_home else f"{title} | {SITE_NAME}"),
        "description": esc(HOME_DESC if is_home else f"{title}: {SITE_NAME}, planetary science, University of Copenhagen."),
        "nav": render_nav(nav_label, root),
        "main": main.rstrip(),
        "wide": " wide" if out in WIDE else "",
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
    themes = tomllib.loads((SRC / "data" / "themes.toml").read_text(encoding="utf-8"))["theme"]
    for out, title, fragment, nav_label in PAGES:
        path = ROOT / out
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_page(template, out, title, fragment, nav_label, pubs, talks, themes), encoding="utf-8")
    ## Tells GitHub Pages to serve these files as they are
    (ROOT / ".nojekyll").touch()
    print(f"Built {len(PAGES)} pages, {len(pubs)} publication entries, {len(talks)} talks.")


if __name__ == "__main__":
    main()
