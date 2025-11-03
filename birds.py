#!/usr/bin/env python

import argparse
import requests
import os
import sys
import time
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser(description="List bird observations")
parser.add_argument("--force-fetch", action="store_true", help="Don't use cached HTML response")
args = parser.parse_args()

script_dir = os.path.dirname(os.path.abspath(__file__))
url = "https://www.artsobservasjoner.no/ViewSighting/ViewSpeciesList?storedSearchCriterias=10026975"
# url = "https://www.artsobservasjoner.no/ViewSighting/ViewSpeciesList?storedSearchCriterias=10657922"
cache_file = os.path.join(script_dir, "cache.html")

def cache_is_fresh():
    if not os.path.exists(cache_file):
        return False
    return os.path.getmtime(cache_file) > time.time() - 3600  # 1 hour

use_cache = cache_is_fresh() and not args.force_fetch

# Fetch data or open cache file
if use_cache:
    sys.stderr.write(f"Using local cache file ({cache_file})\n")
    with open(cache_file, encoding="utf-8") as f:
        html = f.read()
else:
    sys.stderr.write(f"Fetching from {url}\n")
    response = requests.get(url)
    html = response.text
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(html)

soup = BeautifulSoup(html, "html.parser")

# Read and print search parameters
metadata = {
    "tidsperiode": None,
    "locations": [],
    "annet": []
}
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
sys.stdout.write(f"Periode: {metadata['tidsperiode']}\nSted: {', '.join(metadata['locations'])}\n\n")

# Gather birds
birds = []
for list_item in soup.select("ul#taxonlist li.taxon"):
    name_block = list_item.find("span", attrs={"data-taxonid": True})
    if name_block:
        common_name = name_block.find("b").text
        sightings_tag = list_item.select_one(".sightingscount a")
        url = "https://www.artsobservasjoner.no" + sightings_tag["href"]
        count = int(sightings_tag.text)
        birds.append(
            {
                "common": common_name,
                "url": url,
                "count": count,
            }
        )

# Remove skiplisted birds
skiplist_path = os.path.join(script_dir, "skiplist")
with open(skiplist_path, encoding="utf-8") as f:
    skiplist = [line.strip() for line in f]
interesting_birds = [b for b in birds if b["common"] not in skiplist]

# Print birds sorted by common name
for b in sorted(interesting_birds, key=lambda x:x["common"]):
    sys.stdout.write(f"{b["common"]} ({b["count"]}) -- {b["url"]}\n")
