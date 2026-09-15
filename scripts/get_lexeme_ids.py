#!/usr/bin/env python3
# Standalone data-preparation helper: fetches Wikidata language Lexeme IDs and
# generates Quarry SQL under queries/generated/. Its JSON output is not read by
# the live dashboard; monthly numbers are entered manually into the Google Sheet.
"""
Fetch the list of Lexeme IDs (L-ids) for each target language from the
public Wikidata Query Service, cache them under data/lexeme_ids/, and
write ready-to-paste Quarry SQL files under queries/generated/.

This script only talks to query.wikidata.org (public, no auth needed) so
it's safe to run from GitHub Actions, a laptop, or Toolforge.

Usage:
    python3 scripts/get_lexeme_ids.py
"""
import json
import os
import time
import urllib.parse
import urllib.request

LANGUAGES = {
    "Dagbanli": "Q32238",
    "Malayalam": "Q36236",
    "Igbo": "Q33578",
    "Central Bikol": "Q33284",
}

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
CHUNK_SIZE = 3000
START_TIMESTAMP = "20260101000000"  # Jan 2026, matches overall query baseline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDS_DIR = os.path.join(ROOT, "data", "lexeme_ids")
SQL_DIR = os.path.join(ROOT, "queries", "generated")


def fetch_lexeme_ids(qid: str) -> list[str]:
    query = f"""
    SELECT ?lexeme WHERE {{
      ?lexeme dct:language wd:{qid} .
    }}
    """
    url = SPARQL_ENDPOINT + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    req = urllib.request.Request(url, headers={
        "User-Agent": "dagbanli-lexeme-dashboard/1.0 (reporting script)",
        "Accept": "application/sparql-results+json",
    })
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.load(resp)
    ids = []
    for row in data["results"]["bindings"]:
        uri = row["lexeme"]["value"]  # http://www.wikidata.org/entity/L12345
        ids.append(uri.rsplit("/", 1)[-1])
    return sorted(ids, key=lambda x: int(x[1:]))


def write_quarry_sql(lang: str, ids: list[str]):
    safe = lang.lower().replace(" ", "_")
    chunks = [ids[i:i + CHUNK_SIZE] for i in range(0, len(ids), CHUNK_SIZE)]
    for n, chunk in enumerate(chunks, start=1):
        id_list = ",".join(f"'{i}'" for i in chunk)
        sql = f"""-- {lang}: monthly Lexeme edits, chunk {n}/{len(chunks)} ({len(chunk)} lexemes)
-- Paste into https://quarry.wmcloud.org against the "wikidatawiki" database.
SELECT
  LEFT(rev_timestamp, 6) AS month,
  COUNT(*)               AS edit_count
FROM revision
JOIN page
  ON revision.rev_page = page.page_id
WHERE page.page_namespace = 146
  AND page.page_title IN ({id_list})
  AND rev_timestamp >= '{START_TIMESTAMP}'
GROUP BY month
ORDER BY month;
"""
        path = os.path.join(SQL_DIR, f"{safe}_chunk{n}.sql")
        with open(path, "w") as f:
            f.write(sql)
        print(f"  wrote {path} ({len(chunk)} ids)")


def main():
    os.makedirs(IDS_DIR, exist_ok=True)
    os.makedirs(SQL_DIR, exist_ok=True)

    for lang, qid in LANGUAGES.items():
        print(f"Fetching lexeme IDs for {lang} ({qid})...")
        ids = fetch_lexeme_ids(qid)
        print(f"  {len(ids)} lexemes")

        safe = lang.lower().replace(" ", "_")
        with open(os.path.join(IDS_DIR, f"{safe}.json"), "w") as f:
            json.dump({"language": lang, "qid": qid, "count": len(ids), "ids": ids}, f, indent=2)

        write_quarry_sql(lang, ids)
        time.sleep(1)  # be polite to WDQS

    print("Done. Generated SQL is in queries/generated/ — run each file in Quarry.")


if __name__ == "__main__":
    main()
