#!/usr/bin/env python
"""Generate an Atom feed from bird observations."""

import os
import sys
from datetime import date, timezone, datetime
from xml.etree.ElementTree import Element, SubElement, tostring, parse, indent

from scrape import fetch_html, parse_observations, filter_birds

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(SCRIPT_DIR, "docs")
FEED_PATH = os.path.join(DOCS_DIR, "feed.xml")
INDEX_PATH = os.path.join(DOCS_DIR, "index.html")
MAX_ENTRIES = 50
ATOM_NS = "http://www.w3.org/2005/Atom"


def make_entry_id(d):
    """Tag URI that's unique per day — prevents duplicates on re-runs."""
    return f"tag:fugler,{d.isoformat()}:observations"


def build_entry_html(metadata, birds):
    lines = []
    lines.append(f"<p>Periode: {metadata['tidsperiode']}<br>")
    lines.append(f"Sted: {', '.join(metadata['locations'])}</p>")
    lines.append("<ul>")
    for b in sorted(birds, key=lambda x: x["common"]):
        lines.append(f'<li><a href="{b["url"]}">{b["common"]}</a> ({b["count"]})</li>')
    lines.append("</ul>")
    return "\n".join(lines)


def load_existing_entries():
    """Load entries from existing feed file, if any."""
    if not os.path.exists(FEED_PATH):
        return []
    tree = parse(FEED_PATH)
    root = tree.getroot()
    return root.findall(f"{{{ATOM_NS}}}entry")


def build_feed(new_entry_content, today):
    root = Element("feed", xmlns=ATOM_NS)

    SubElement(root, "title").text = "Fugleobservasjoner"
    SubElement(root, "id").text = "tag:fugler,2026:feed"
    SubElement(root, "updated").text = datetime.now(timezone.utc).isoformat()
    SubElement(root, "link", rel="self", href="https://mortenfyhn.github.io/birdbot/feed.xml")

    # New entry
    entry = SubElement(root, "entry")
    SubElement(entry, "title").text = f"Observasjoner {today.isoformat()}"
    SubElement(entry, "id").text = make_entry_id(today)
    SubElement(entry, "updated").text = datetime.now(timezone.utc).isoformat()
    content = SubElement(entry, "content", type="html")
    content.text = new_entry_content

    # Carry over old entries (skip if same date — replace)
    today_id = make_entry_id(today)
    existing = load_existing_entries()
    kept = 0
    for old_entry in existing:
        old_id = old_entry.find(f"{{{ATOM_NS}}}id")
        if old_id is not None and old_id.text == today_id:
            continue
        root.append(old_entry)
        kept += 1
        if kept >= MAX_ENTRIES - 1:
            break

    return root


def write_index(metadata):
    location_items = "\n".join(f"    <li>{loc}</li>" for loc in metadata["locations"])
    period = metadata["tidsperiode"].lower()
    html = f"""<!DOCTYPE html>
<html lang="nb">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Birdbot</title>
  <link rel="alternate" type="application/atom+xml" title="Birdbot" href="feed.xml">
</head>
<body>
  <h1>Birdbot</h1>
  <p>Interessante fugleobservasjoner fra</p>
  <ul>
{location_items}
  </ul>
  <p>de {period}.</p>
  <p><a href="feed.xml">Abonner (RSS)</a></p>
</body>
</html>
"""
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    html = fetch_html()
    metadata, birds = parse_observations(html)
    interesting = filter_birds(birds)

    if not interesting:
        sys.stderr.write("No interesting birds today, skipping feed update.\n")
        return

    today = date.today()
    entry_html = build_entry_html(metadata, interesting)
    feed = build_feed(entry_html, today)

    indent(feed)
    xml_bytes = tostring(feed, encoding="unicode", xml_declaration=True)
    with open(FEED_PATH, "w", encoding="utf-8") as f:
        f.write(xml_bytes)

    write_index(metadata)
    sys.stderr.write(f"Feed updated: {FEED_PATH}\n")


if __name__ == "__main__":
    main()
