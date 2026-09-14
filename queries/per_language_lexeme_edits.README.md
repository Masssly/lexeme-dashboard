# Per-language monthly Lexeme edits

The wikireplica database (what Quarry queries) does **not** store a lexeme's
language as a queryable column — language is just a regular statement
(`dct:language` → a language item), living inside the entity's JSON/RDF, not
in `page`/`revision`. So there's no single SQL query that can filter
"Lexeme edits WHERE language = Dagbanli" directly.

The standard two-step workaround:

1. **Get the list of Lexeme IDs (L-ids) for a language**, via SPARQL against
   the public Wikidata Query Service (query.wikidata.org) — this data
   (current language assignment) *is* available there.
2. **Feed that ID list into a Quarry query** that filters
   `page.page_title IN (...)` and groups by month, same shape as the overall
   query.

`scripts/get_lexeme_ids.py` in this repo does step 1 and also writes ready-
to-paste Quarry SQL files into `queries/generated/`, chunked (default 3,000
IDs per file) so the query text doesn't get unwieldy for large languages
like Malayalam. For Dagbanli, Igbo, and Central Bikol (each a few thousand
lexemes) you'll likely get just one file per language.

Run each generated file in Quarry, note the monthly totals, and — if a
language needed more than one chunk — add the counts for the same month
across its chunk files together.

This repo's `scripts/toolforge_update_stats.py` automates both steps end to
end (see main README) — it's the better option once you have Toolforge
access, since it skips the manual copy/paste entirely.

## Language QIDs used

| Language      | QID    |
|---------------|--------|
| Dagbanli      | Q32238 |
| Malayalam     | Q36236 |
| Igbo          | Q33578 |
| Central Bikol | Q33284 |
