# SwoleMate backend — Supabase Edge Functions (backup mirror)

This folder is the **backup of the live edge functions** running on Supabase project
`lxuvaggznyvgqxknlnvp`. The functions that actually run live on Supabase; **this repo does
NOT auto-sync with them.** If a function is redeployed and nobody commits it here, this
backup silently goes stale.

> ⚠️ Lesson (2026-07-18): before this snapshot, 4 live functions (`onboard`, `cron-message`,
> `goals-app`, `gen-avatar`) had **no backup at all**, and the 6 that were here were months
> out of date (e.g. `oura-oauth` was still the old primary-only version). The local Google
> Drive copies were stale too. Only Supabase itself was correct.

## The functions (10)

| Function | What it does |
|---|---|
| `onboard` | Backend for the hosted `onboard.html` setup page (goals + profile). |
| `connect` | Backend for the direct Oura/Cronometer login section + `connect.html`. |
| `goals-app` | Older primary-only goals form/API (superseded by `onboard`). |
| `oura-oauth` | Oura OAuth start + callback; stores per-user Oura tokens. |
| `cron-pull` | Scrapes Cronometer (food + gym + cardio) into the DB. |
| `cron-pull-oura` | Pulls Oura daily activity + workouts into the DB. |
| `ingest-health` | Catches Apple Health data from the iOS Shortcut. |
| `cron-message` | Older WhatsApp daily-checkin sender (template-based). |
| `coach` | The engine: daily read, week-so-far, close-the-gap, meal checks, ladders, season. |
| `gen-avatar` | Calls Gemini image model to turn a photo into a cartoon avatar. |

## Keep this backup current — the habit

**After ANY edge-function deploy, mirror it here in the same session:**

1. Pull the live source of the function(s) you changed
   (Supabase MCP `get_edge_function`, or `supabase functions download <slug>` if the CLI is installed).
2. Overwrite the matching `src/supabase-functions/<slug>/index.ts` (+ any extra files, e.g. `coach/roast-lines.ts`).
3. `git add -A && git commit -m "backup: <slug> vN" && git push`.

Rule of thumb: **a deploy isn't done until it's committed here.** A stale backup that looks
current is worse than no backup.

## Restoring

To redeploy from this backup, deploy each `<slug>/index.ts` (with its sibling files) back to the
same slug on the Supabase project. Secrets (DB URL, WhatsApp, Oura, Gemini, Cronometer creds)
live in Supabase env vars and are **not** in this repo — they must already be set on the project.
