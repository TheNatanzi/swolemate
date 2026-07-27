// cron-pull-oura v10 (2026-07) — sessions + enhanced_tags now count as workouts (needs oura-oauth v10 scopes:
// session tag heartrate). Exercise-looking sessions/tags are classified like workouts (strength -> gym, else -> cardio);
// non-exercise ones (nap, meditation, mood tags…) are ignored. Items overlapping an existing /workout entry are
// deduped so the same HIIT doesn't count twice. Duration-less exercise tags default to 30m (name marked with ~).
// v9: adds ?raw=1 debug: dumps raw /workout + /session + /enhanced_tag (with minutes) per user, no writes.
// v8: Oura writes gym/cardio ONLY when Cronometer isn't the workout source (primary OR food_only=false skip). Steps land for everyone.
// v7: workouts classified server-side — strength-type -> gym_log sessions, everything else -> cardio_log minutes (non-primary only).
import postgres from "https://deno.land/x/postgresjs@v3.4.5/mod.js";

const TOKEN = "https://api.ouraring.com/oauth/token";
const API = "https://api.ouraring.com/v2/usercollection";

function laDate(offsetDays = 0) {
  const d = new Date(Date.now() + offsetDays * 86400000);
  return new Intl.DateTimeFormat("en-CA", { timeZone: "America/Los_Angeles" }).format(d);
}

const GYM_RX = /strength|weight|functional|cross[_\s-]?train|resistance|powerlift|bodybuild/i;
const EXERCISE_RX = /hiit|interval|cardio|run|jog|sprint|cycl|bik(e|ing)|swim|row|walk|hik(e|ing)|elliptical|spin|box|kick|danc|aerobic|sport|soccer|football|basketball|tennis|padel|squash|climb|jump|skat|ski|surf|yoga|pilates|stretch|exercise|workout|train|circuit|bootcamp|core|abs/i;
const pretty = (s) => String(s ?? "").replace(/^tag_(generic|activity)_/, "").replace(/_/g, " ").trim();
const spanMin = (a, b) => { const t0 = Date.parse(a), t1 = Date.parse(b); return (Number.isFinite(t0) && Number.isFinite(t1) && t1 > t0) ? Math.round((t1 - t0) / 60000) : null; };
const wkMin = (w) => spanMin(w.start_datetime, w.end_datetime);

// Normalize workouts + sessions + tags into {day, name, min, start, kind}, dedupe overlaps, bucket per day.
function classifyItems(workouts, sessions, tags) {
  const items = [];
  for (const w of workouts) {
    const day = w.day ?? String(w.start_datetime ?? "").slice(0, 10);
    if (!day) continue;
    items.push({ day, name: pretty(w.activity || w.label || "workout"), min: wkMin(w) ?? 0, start: Date.parse(w.start_datetime), kind: "workout" });
  }
  for (const s of sessions) {
    const day = s.day ?? String(s.start_datetime ?? "").slice(0, 10);
    const name = pretty(s.type);
    if (!day || !(GYM_RX.test(name) || EXERCISE_RX.test(name))) continue; // skip meditation/nap/rest etc.
    items.push({ day, name, min: spanMin(s.start_datetime, s.end_datetime) ?? 0, start: Date.parse(s.start_datetime), kind: "session" });
  }
  for (const t of tags) {
    const day = t.start_day ?? t.day ?? String(t.start_time ?? "").slice(0, 10);
    const name = pretty(t.tag_type_code ?? t.comment);
    if (!day || !(GYM_RX.test(name) || EXERCISE_RX.test(name))) continue; // skip mood/food/etc. tags
    const min = spanMin(t.start_time, t.end_time);
    items.push({ day, name: min == null ? `${name}~` : name, min: min ?? 30, start: Date.parse(t.start_time), kind: "tag" });
  }
  // Dedupe: drop sessions/tags starting within 45m of a /workout entry the same day (same activity, two records).
  const wkStarts = items.filter((i) => i.kind === "workout");
  const deduped = items.filter((i) => i.kind === "workout" ||
    !wkStarts.some((w) => w.day === i.day && Number.isFinite(i.start) && Number.isFinite(w.start) && Math.abs(w.start - i.start) < 45 * 60000));
  const byDay = {};
  for (const i of deduped) {
    if (i.min > 240) continue; // all-day noise
    const d = (byDay[i.day] ??= { gymSessions: 0, gymMin: 0, gymNames: [], cardioMin: 0, cardioNames: [], count: 0 });
    d.count++;
    if (GYM_RX.test(i.name)) { d.gymSessions++; d.gymMin += i.min; d.gymNames.push(i.name); }
    else { d.cardioMin += i.min; d.cardioNames.push(`${i.name} ${i.min}m`); }
  }
  return byDay;
}

Deno.serve(async (req) => {
  const url = new URL(req.url);
  const start = url.searchParams.get("start") ?? laDate(-1);
  const end = url.searchParams.get("end") ?? laDate(0);
  const dryRun = url.searchParams.get("dry") === "1";
  const raw = url.searchParams.get("raw") === "1";
  const clientId = Deno.env.get("OURA_CLIENT_ID");
  const clientSecret = Deno.env.get("OURA_CLIENT_SECRET");
  const sql = postgres(Deno.env.get("SUPABASE_DB_URL"), { prepare: false });
  try {
    const users = await sql`select ot.user_id, ot.refresh_token, ot.access_token, ot.expires_at, au.display_name, au.cronometer_ref, ca.food_only
                            from fitness.oura_token ot join fitness.app_user au on au.id = ot.user_id
                            left join fitness.cronometer_account ca on ca.user_id = au.id`;
    const results = [];
    for (const u of users) {
      let access = u.access_token;
      if (!access || !u.expires_at || new Date(u.expires_at).getTime() < Date.now() + 5 * 60000) {
        const r = await fetch(TOKEN, {
          method: "POST",
          headers: { "content-type": "application/x-www-form-urlencoded", "Authorization": "Basic " + btoa(`${clientId}:${clientSecret}`) },
          body: new URLSearchParams({ grant_type: "refresh_token", refresh_token: u.refresh_token }).toString(),
        });
        const tok = await r.json().catch(() => ({}));
        if (!tok.access_token) { results.push({ user: u.display_name, error: "refresh failed", body: tok }); continue; }
        access = tok.access_token;
        const expires = new Date(Date.now() + (tok.expires_in ?? 86400) * 1000).toISOString();
        await sql`update fitness.oura_token set access_token = ${tok.access_token}, refresh_token = ${tok.refresh_token}, expires_at = ${expires}, updated_at = now() where user_id = ${u.user_id}`;
      }
      const hdr = { Authorization: `Bearer ${access}` };
      const grab = async (path) => await (await fetch(`${API}/${path}?start_date=${start}&end_date=${end}`, { headers: hdr })).json().catch((e) => ({ err: String(e) }));
      const wk = await grab("workout");
      const sess = await grab("session");
      const tags = await grab("enhanced_tag");

      if (raw) {
        results.push({ user: u.display_name,
          workouts: (wk.data ?? []).map((w) => ({ day: w.day, activity: w.activity, label: w.label, source: w.source, intensity: w.intensity, min: wkMin(w), start: w.start_datetime })),
          sessions: (sess.data ?? []).map((s) => ({ day: s.day, type: s.type, min: spanMin(s.start_datetime, s.end_datetime), start: s.start_datetime })),
          tags: (tags.data ?? []).map((t) => ({ day: t.start_day ?? t.day, tag: t.tag_type_code ?? t.comment, min: spanMin(t.start_time, t.end_time), start: t.start_time })),
          errors: { workout: wk.data ? undefined : wk, session: sess.data ? undefined : sess, tag: tags.data ? undefined : tags } });
        continue;
      }

      const act = await grab("daily_activity");
      const byDay = classifyItems(wk.data ?? [], sess.data ?? [], tags.data ?? []);
      const writeWk = u.cronometer_ref !== "primary" && u.food_only !== false;
      let written = 0, gymRows = 0, cardioRows = 0;
      if (!dryRun) {
        for (const d of act.data ?? []) {
          await sql`insert into fitness.activity_log (user_id, log_date, steps, workouts, active_calories, raw) values (${u.user_id}, ${d.day}, ${d.steps ?? null}, ${byDay[d.day]?.count ?? 0}, ${d.active_calories ?? null}, ${sql.json(d)})`;
          written++;
        }
        if (writeWk) {
          for (const [day, d] of Object.entries(byDay)) {
            await sql`insert into fitness.gym_log (user_id, log_date, sessions, minutes, names, raw) values (${u.user_id}, ${day}, ${d.gymSessions}, ${d.gymMin}, ${d.gymNames.length ? d.gymNames : ["oura"]}, ${sql.json({ source: "oura", day, workouts: d })})`;
            gymRows++;
            await sql`insert into fitness.cardio_log (user_id, log_date, minutes, names, raw) values (${u.user_id}, ${day}, ${Math.round(d.cardioMin)}, ${d.cardioNames.length ? d.cardioNames : ["oura"]}, ${sql.json({ source: "oura", day, workouts: d })})`;
            cardioRows++;
          }
        }
      }
      results.push({ user: u.display_name, days: written, gym_cardio_days: writeWk ? { gym: gymRows, cardio: cardioRows } : "skipped (Cronometer is workout source)", classified: byDay });
    }
    return Response.json({ ok: true, dry: dryRun, raw, range: { start, end }, results });
  } catch (e) {
    return Response.json({ ok: false, error: String(e instanceof Error ? e.message : e) }, { status: 500 });
  } finally {
    try { await sql.end(); } catch { /* ignore */ }
  }
});
