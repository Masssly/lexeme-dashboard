# Wikidata Lexeme Edit Dashboard

A lightweight GitHub Pages dashboard for tracking the Wikidata Lexeme-editing KR:

> The average number of monthly edits on Lexemes reaches 80,000 across Q3 and Q4 (baseline January-March 2026: 66,670). As priority languages for Abstract Wikipedia are identified, efforts are progressively focused on these languages.

The live dashboard shows overall monthly Lexeme edits and a per-language view for four priority languages:

- Dagbanli
- Malayalam
- Igbo
- Central Bikol

## How the live pipeline works

The **Google Sheet is the source of truth** for dashboard data. The sheet URL/ID is kept in `.github/workflows/sync-google-sheet.yml` rather than hardcoded here.

```text
Google Sheet
    │
    │ scheduled sync or manual trigger
    ▼
.github/workflows/sync-google-sheet.yml
    │
    │ fetches the Sheet's gviz CSV export
    ▼
data/dashboard.csv
    │
    │ push to main triggers Pages deployment
    ▼
.github/workflows/pages.yml
    │
    ▼
GitHub Pages → index.html + data/
```

### Automatic updates

`sync-google-sheet.yml` runs on a schedule and can also be started manually with GitHub Actions. When the Sheet has changed, the workflow replaces `data/dashboard.csv` and commits the updated file to `main`. That push starts `pages.yml`, which publishes the current dashboard to GitHub Pages.

### Manual updates

Open `sync.html` from the dashboard when you want to start a sync immediately. It provides the authenticated entry point to the `sync-google-sheet.yml` GitHub Actions workflow. GitHub authenticates you before you can dispatch the workflow.

The sync workflow then:

1. Fetches the latest Google Sheet CSV export server-side.
2. Writes `data/dashboard.csv`.
3. Commits the file only when the data has changed.
4. Lets `pages.yml` deploy the updated dashboard automatically.

No Google Sheet credentials are stored in the repository.

## Dashboard projection

The overall chart has an optional **Show Q4 projection** toggle. The projection extends the chart from the latest available actual month through December 2026.

The current projection is deliberately simple: it fits a linear trend to the available July-September 2026 actuals and uses that trend to estimate the remaining Q4 months. The projected October, November and December values are also shown below the chart, together with the projected Q4 average.

This is an indicator for planning and discussion, not a statistical forecast or a change to the KR. The projection uses only data already present in `data/dashboard.csv` and does not alter the source data.

## Getting real numbers into the Sheet

The repository also contains standalone helpers for producing the data that is entered into the Google Sheet. **This is a manual data-preparation workflow, not part of the automated GitHub Pages pipeline.**

### 1. Generate language Lexeme ID lists and Quarry SQL

Run:

```bash
python3 scripts/get_lexeme_ids.py
```

The script queries the public Wikidata Query Service for Lexeme IDs belonging to each target language and generates ready-to-paste Quarry SQL under `queries/generated/`.

For large language ID lists, the SQL is split into chunks. Run the generated queries in Quarry against `wikidatawiki` and use the resulting monthly counts when updating the Sheet.

### 2. Enter the numbers in the Google Sheet

Copy the relevant monthly overall and per-language counts into the Sheet manually. The Sheet is the source of truth. **Do not edit `data/dashboard.csv` by hand as the normal data-entry method**; the sync workflow regenerates it from the Sheet.

`scripts/toolforge_update_stats.py` is retained as a standalone/legacy helper for fetching language IDs and querying the Wikimedia replica database. Its JSON output belongs to the old data pipeline and is **not consumed by the live dashboard**. It does not populate the Google Sheet automatically.

## CSV schema

The synced file is `data/dashboard.csv`. It must contain these columns:

```text
month, overall_edits, dagbanli, malayalam, igbo, central_bikol
```

The underlying Google Sheet uses the same column names. `month` is represented as `YYYY-MM` (for example, `2026-01`), while the edit columns contain numeric monthly counts.

## Dashboard files

```text
index.html                              Live dashboard
sync.html                               Human-facing manual sync entry point
data/dashboard.csv                     Synced dashboard data
.github/workflows/sync-google-sheet.yml Sheet → CSV sync
.github/workflows/pages.yml             GitHub Pages deployment
queries/                                Quarry SQL and generation notes
queries/generated/                      Generated per-language Quarry SQL
scripts/get_lexeme_ids.py               WDQS → Lexeme IDs → Quarry SQL helper
scripts/toolforge_update_stats.py       Standalone/legacy replica-data helper
```

## Language QIDs

| Language | QID |
|---|---|
| Dagbanli | Q32238 |
| Malayalam | Q36236 |
| Igbo | Q33578 |
| Central Bikol | Q33284 |

## Live dashboard

[Open the Lexeme Edit Dashboard](https://masssly.github.io/lexeme-dashboard/)
