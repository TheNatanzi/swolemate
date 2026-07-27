// cron-pull-oura v7 — pulls Oura daily activity + workouts for every connected user (fitness.oura_token).
// v7: workouts are classified server-side — strength-type -> gym_log sessions, everything else -> cardio_log
//     minutes — for NON-primary users only. The primary user's gym/cardio come from Cronometer (cron-pull);
//     writing both sources would race in the v_*_latest views. Steps/workout counts still land in activity_log
//     for everyone. &dry=1 returns the classification without writing.
import postgres from "https://deno.land/x/postgresjs@v3.4.5/mod.js";

const TOKEN = "https://api.ouraring.com/oauth/token";
const API = "https://api.ouraring.com/v2/usercollection";

function laDate(offsetDays = 0) {
  const d = new Date(Date.now() + offsetDays * 86400000);
  return new Intl.DateTimeFormat("en-CA", { timeZone: "America/Los_Angeles" }).format(d);
}

const GYM_RX = /strength|weight|functional|cross[_\s-]?train|resistance|powerlift|bodybuild/i;
const pretty = (s) => String(s ?? "").replace(/_/g, " ").trim();
function classifyWorkouts(list) {
  const byDay = {};
  for (const w of list) {
    const day = w.day ?? String(w.start_datetime ?? "").slice(0, 10);
    if (!day) continue;
    const name = pretty(w.activity || w.label || "workout");
    let min = 0;
    const t0 = Date.parse(w.start_datetime), t1 = Date.parse(w.end_datetime);
    if (Number.isFinite(t0) && Number.isFinite(t1) && t1 > t0) min = Math.round((t1 - t0) / 60000);
    if (min > 240) continue; // all-day noise
    const d = (byDay[day] ??= { gymSessions: 0, gymMin: 0, gymNames: [], cardioMin: 0, cardioNames: [], count: 0 });
    d.count++;
    if (GYM_RX.test(name)) { d.gymSessions++; d.gymMin += min; d.gymNames.push(name); }
    else { d.cardioMin += min; d.cardioNames.push(`${name} ${min}m`); }
  }
  return byDay;
}

Deno.serve(async (req) => {
  const url = new URL(req.url);
  const start = url.searchParams.get("start") ?? laDate(-1);
  const end = url.searchParams.get("end") ?? laDate(0);
  const dryRun = url.searchParams.get("dry") === "1";
  const clientId = Deno.env.get("OURA_CLIENT_ID");
  const clientSecret = Deno.env.get("OURA_CLIENT_SECRET");
  const sql = postgres(Deno.env.get("SUPABASE_DB_URL"), { prepare: false });
  try {
    const users = await sql`select ot.user_id, ot.refresh_token, ot.access_token, ot.expires_at, au.display_name, au.cronometer_ref
                            from fitness.oura_token ot join fitness.app_user au on au.id = ot.user_id`;
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
      const act = await (await fetch(`${API}/daily_activity?start_date=${start}&end_date=${end}`, { headers: hdr })).json().catch(() => ({}));
      const wk = await (await fetch(`${API}/workout?start_date=${start}&end_date=${end}`, { headers: hdr })).json().catch(() => ({}));
      const byDay = classifyWorkouts(wk.data ?? []);
      const writeWk = u.cronometer_ref !== "primary"; // primary's gym/cardio come from Cronometer
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
      results.push({ user: u.display_name, days: written, gym_cardio_days: writeWk ? { gym: gymRows, cardio: cardioRows } : "skipped (primary uses Cronometer)", classified: byDay, debug: (act.data ? undefined : act) });
    }
    return Response.json({ ok: true, dry: dryRun, range: { start, end }, results });
  } catch (e) {
    return Response.json({ ok: false, error: String(e instanceof Error ? e.message : e) }, { status: 500 });
  } finally {
    try { await sql.end(); } catch { /* ignore */ }
  }
});
