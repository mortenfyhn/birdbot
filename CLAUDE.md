# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a bird observation notification system that scrapes data from artsobservasjoner.no (Norwegian species observation database) and publishes interesting sightings as an Atom feed. The system runs on Semaphore CI to provide scheduled updates, served via GitHub Pages.

## Core Architecture

1. **scrape.py** - Scraper library and CLI:
   - Fetches HTML from artsobservasjoner.no (with 1-hour caching)
   - Parses bird observations using BeautifulSoup
   - Filters out common birds using the `skiplist` file
   - Exposes `fetch_html()`, `parse_observations()`, `filter_birds()` for reuse
   - CLI outputs formatted list of interesting birds to stdout

2. **publish_feed.py** - Atom feed publisher:
   - Imports scraping functions from scrape.py
   - Generates/updates `docs/feed.xml` with one entry per run (digest of all interesting birds)
   - Keeps last 50 entries, deduplicates by date

3. **publish_telegram.sh** - Legacy Telegram publisher (may be removed):
   - Runs scrape.py and sends output to Telegram via bot API
   - Requires TOKEN and CHAT_ID environment variables

## Dependencies

Install required Python packages:
```bash
pip install bs4 requests
```

## Running Locally

Run the scraper:
```bash
./scrape.py
```

Force fresh data (bypass cache):
```bash
./scrape.py --force-fetch
```

Generate the Atom feed:
```bash
python publish_feed.py
```

## Key Files

- **skiplist**: Contains Norwegian bird names (one per line) to filter out common species
- **cache.html**: 1-hour cache of fetched HTML (gitignored)
- **docs/feed.xml**: Generated Atom feed (committed by CI, served by GitHub Pages)
- **docs/index.html**: Landing page with feed subscription link
- **.semaphore/semaphore.yml**: CI configuration that runs the feed publisher on schedule

## Important Implementation Details

- The script uses a hardcoded search URL (in scrape.py) that references a stored search on artsobservasjoner.no
- Bird names in the skiplist must exactly match the Norwegian common names from the website
- The cache mechanism checks file modification time; cache is considered stale after 1 hour
- Feed entry IDs use tag URIs based on date — re-running on the same day replaces that day's entry
- Bird quotes in the output must use single quotes, not typographic quotes (this was a previous bug)
