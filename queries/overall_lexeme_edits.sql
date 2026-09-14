-- Run this on https://quarry.wmcloud.org against the "wikidatawiki" database.
-- Counts ALL revisions (edits) in the Lexeme namespace (146) per calendar month,
-- since January 2026. Includes bot edits (Wikidata Lexeme growth is heavily
-- bot/tool-assisted, e.g. Lexeme Forms, QuickStatements, so excluding bots would
-- undercount real community-driven progress unless you specifically want human-only).
--
-- If you want to exclude a specific bot account, add:
--   AND actor_name NOT IN ('SomeBotName')
-- and JOIN actor ON revision.rev_actor = actor.actor_id

SELECT
  LEFT(rev_timestamp, 6) AS month,      -- YYYYMM
  COUNT(*)               AS edit_count
FROM revision
JOIN page
  ON revision.rev_page = page.page_id
WHERE page.page_namespace = 146         -- Lexeme namespace
  AND rev_timestamp >= '20260101000000'
GROUP BY month
ORDER BY month;
