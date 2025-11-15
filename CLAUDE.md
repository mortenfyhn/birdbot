# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a bird observation notification system that scrapes data from artsobservasjoner.no (Norwegian species observation database) and sends alerts about interesting bird sightings via Telegram. The system runs on Semaphore CI to provide scheduled notifications.

## Core Architecture

The system consists of two main scripts:

1. **birds.py** - Main scraper that:
   - Fetches HTML from artsobservasjoner.no (with 1-hour caching)
   - Parses bird observations using BeautifulSoup
   - Filters out common birds using the `skiplist` file
   - Outputs formatted list of interesting birds to stdout

2. **birdbot.sh** - Telegram notification wrapper that:
   - Runs birds.py and captures output
   - Sends results to Telegram using bot API
   - Requires TOKEN and CHAT_ID environment variables

## Dependencies

Install required Python packages:
```bash
pip install bs4 requests
```

## Running Locally

Run the scraper:
```bash
./birds.py
```

Force fresh data (bypass cache):
```bash
./birds.py --force-fetch
```

Send to Telegram (requires env vars):
```bash
export TOKEN="your-telegram-bot-token"
export CHAT_ID="your-chat-id"
./birdbot.sh
```

## Key Files

- **skiplist**: Contains Norwegian bird names (one per line) to filter out common species
- **cache.html**: 1-hour cache of fetched HTML (gitignored)
- **.semaphore/semaphore.yml**: CI configuration that runs the bot on schedule

## Important Implementation Details

- The script uses a hardcoded search URL (line 17 in birds.py) that references a stored search on artsobservasjoner.no
- Bird names in the skiplist must exactly match the Norwegian common names from the website
- The cache mechanism checks file modification time; cache is considered stale after 1 hour
- Output format includes period, location, and bird list with sighting counts and URLs
- Bird quotes in the output must use single quotes, not typographic quotes (this was a previous bug)
