# App Review Analysis

Scrapes iOS App Store and Google Play reviews by app name and date range, then runs LLM-powered analysis to surface themes, sentiment breakdowns, and prioritized product recommendations for product managers.

## Features

- **Automatic app lookup** — search by name, no app IDs needed
- **Dual-store scraping** — App Store (via Apple RSS) and Google Play
- **Theme discovery** — LLM identifies recurring topics specific to the app
- **Sentiment analysis** — per-theme breakdown with avg ratings
- **PM briefing** — structured report with Fix Now / Improve / Feature Requests / What's Working sections
- **Store comparison** — see what iOS vs Android users complain about differently
- **Multi-provider** — supports Anthropic (Claude) and Google Gemini

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key   # or GEMINI_API_KEY for free tier
```

## Usage

```bash
# Full run — scrape + analyze
python3 main.py --app-name "Instagram" --start 2026-01-01 --end 2026-06-01

# Re-run analysis on already-scraped reviews
python3 main.py --app-name "Instagram" --start 2026-01-01 --end 2026-06-01 --skip-scrape

# Use Gemini instead of Claude
python3 main.py --app-name "Instagram" --start 2026-01-01 --end 2026-06-01 --provider gemini

# Scrape only
python3 main.py --app-name "Instagram" --start 2026-01-01 --end 2026-06-01 --skip-analysis
```

## Output

- `reviews.json` — raw scraped reviews (normalized schema)
- `report.md` — PM briefing with themes, priorities, and recommendations
- `report_stats.json` — structured stats for further processing

## Options

| Flag | Default | Description |
|---|---|---|
| `--app-name` | required | App name to search for |
| `--start` | required | Start date (YYYY-MM-DD) |
| `--end` | required | End date (YYYY-MM-DD) |
| `--country` | `us` | Store country code |
| `--provider` | `anthropic` | LLM provider (`anthropic` or `gemini`) |
| `--output` | `reviews.json` | Raw reviews output file |
| `--report` | `report.md` | Report output file |
| `--skip-scrape` | false | Reuse existing reviews file |
| `--skip-analysis` | false | Scrape only, no LLM analysis |
