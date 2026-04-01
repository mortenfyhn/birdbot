#!/usr/bin/env python

import argparse
import requests
import os
import sys
import time
from bs4 import BeautifulSoup

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# url = "https://www.artsobservasjoner.no/ViewSighting/ViewSpeciesList?storedSearchCriterias=10026975"  # Trondheim, Melhus, Malvik
URL = "https://www.artsobservasjoner.no/ViewSighting/ViewSpeciesList?storedSearchCriterias=12664633"  # + Stjørdal, Orkland
CACHE_FILE = os.path.join(SCRIPT_DIR, "cache.html")
SKIPLIST_PATH = os.path.join(SCRIPT_DIR, "skiplist")


def cache_is_fresh():
    if not os.path.exists(CACHE_FILE):
        return False
    return os.path.getmtime(CACHE_FILE) > time.time() - 3600  # 1 hour


def fetch_html(force_fetch=False):
    if cache_is_fresh() and not force_fetch:
        sys.stderr.write(f"Using local cache file ({CACHE_FILE})\n")
        with open(CACHE_FILE, encoding="utf-8") as f:
            return f.read()

    sys.stderr.write(f"Fetching from {URL}\n")
    response = requests.get(URL)
    html = response.text
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    return html


def parse_observations(html):
    """Returns (metadata, birds) from the HTML."""
    soup = BeautifulSoup(html, "html.parser")

    metadata = {"tidsperiode": None, "locations": []}
    for li in soup.select("ul.taglist li.selectedUserFilter"):
        key = li.get("data-label", "")
        value = li.select_one("strong")
        if not value:
            continue
        text = value.text.strip()

        if key.startswith("LastNumberOfDays"):
            metadata["tidsperiode"] = text
        elif key.startswith("Area_"):
            metadata["locations"].append(text)

    birds = []
    for list_item in soup.select("ul#taxonlist li.taxon"):
        name_block = list_item.find("span", attrs={"data-taxonid": True})
        if name_block:
            common_name = name_block.find("b").text
            sightings_tag = list_item.select_one(".sightingscount a")
            url = "https://www.artsobservasjoner.no" + sightings_tag["href"]
            count = int(sightings_tag.text)
            birds.append({"common": common_name, "url": url, "count": count})

    return metadata, birds


def filter_birds(birds):
    with open(SKIPLIST_PATH, encoding="utf-8") as f:
        skiplist = [line.strip() for line in f]
    return [b for b in birds if b["common"] not in skiplist]


def format_output(metadata, birds):
    lines = [f"Periode: {metadata['tidsperiode']}", f"Sted: {', '.join(metadata['locations'])}", ""]
    for b in sorted(birds, key=lambda x: x["common"]):
        lines.append(f"{b['common']} ({b['count']}) — {b['url']}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List bird observations")
    parser.add_argument(
        "--force-fetch", action="store_true", help="Don't use cached HTML response"
    )
    args = parser.parse_args()

    html = fetch_html(force_fetch=args.force_fetch)
    metadata, birds = parse_observations(html)
    interesting = filter_birds(birds)
    sys.stdout.write(format_output(metadata, interesting))
