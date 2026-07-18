// ingest-health v8 — catches phone health data from a Shortcut, writes to the tables the coach reads.
// Accepts: steps, workouts/gym, calories, protein, cardio_min (cardio minutes for cardio-metric users).
// v7: workouts also insert into gym_log (sessions) so shortcut friends can score their gym point — coach reads v_gym_latest, which only sees gym_log.
// v8: wk=<one workout per line, "Name|Duration"> — server classifies each workout: strength-type -> gym session,
//     everything else -> cardio minutes. Explicit workouts/cardio_min params still win over the derived values.
//     &dry=1 skips all DB writes and returns the classification (for testing a Shortcut without polluting logs).
// WEEK LOCK: dates before this week's Monday are rejected (grace: Monday before 12pm LA still accepts last week,
// so Sunday-night data can land before the noon recap). No retroactive edits once the week is over.
import postgres from "https://deno.land/x/postgresjs@v3.4.5/mod.js";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type",
};
const json = (b, s = 200) => new Response(JSON.stringify(b), { status: s, headers: { ...CORS, "content-type": "application/json" } });
const laDate = () => new Intl.DateTimeFormat("en-CA", { timeZone: "America/Los_Angeles" }).format(new Date());
const laHour = () => parseInt(new Intl.DateTimeFormat("en-US", { timeZone: "America/Los_Angeles", hour12: false, hour: "2-digit" }).format(new Date()), 10);
const addDays = (s, n) => { const d = new Date(s + "T12:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
const toInt = (v) => { const n = parseInt(String(v ?? "").replace(/[^\d]/g, ""), 10); return Number.isFinite(n) ? n : null; };
const toNum = (v) => { const n = parseFloat(String(v ?? "").replace(/[^\d.]/g, "")); return Number.isFinite(n) ? n : null; };
const pick = (o, ...keys) => { for (const k of keys) if (o[k] !== undefined && o[k] !== null && o[k] !== "") return o[k]; return null; };

// --- workout classification (v8) ---
// Shortcuts sends Duration as "45", "45 min", "2,700 sec", "42:16" (mm:ss) or "1:02:33" (h:mm:ss) depending on device settings — accept all.
const toMinutes = (s) => {
  const t = String(s ?? "").trim().replace(/,/g, "");
  if (!t) return 0;
  if (t.includes(":")) {
    const p = t.split(":").map((x) => parseFloat(x) || 0);
    return p.length >= 3 ? p[0] * 60 + p[1] + p[2] / 60 : p[0] + p[1] / 60;
  }
  const n = parseFloat(t.replace(/[^\d.]/g, ""));
  if (!Number.isFinite(n)) return 0;
  if (/sec/i.test(t)) return n / 60;
  if (/\bh(ou)?r/i.test(t)) return n * 60;
  return n > 300 ? n / 60 : n; // unlabeled number over 300 = seconds (no single workout runs 5+ hours)
};
const GYM_RX = /strength|weight|functional|core\s*training|cross\s*training/i;
function parseWk(raw) {
  const gym = [], cardio = [];
  for (const line of String(raw).split(/[\n;]/)) {
    const t = line.trim();
    if (!t) continue;
    let name = t, dur = "";
    const bar = t.indexOf("|");
    if (bar >= 0) { name = t.slice(0, bar).trim(); dur = t.slice(bar + 1).trim(); }
    else { const m = t.match(/^(.+?),\s*([\d.,:]+\s*\w*)$/); if (m) { name = m[1].trim(); dur = m[2].trim(); } }
    const min = Math.round(toMinutes(dur) * 10) / 10;
    (GYM_RX.test(name) ? gym : cardio).push({ name, min });
  }
  return { gym, cardio };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  const url = new URL(req.url);
  const q = Object.fromEntries(url.searchParams.entries());
  const token = q.u ?? "";
  const sql = postgres(Deno.env.get("SUPABASE_DB_URL"), { prepare: false });
  try {
    if (!token) return json({ ok: false, error: "missing ?u=<token>" }, 400);

    let body = {};
    if (req.method === "POST") body = await req.json().catch(() => ({}));
    const src = { ...body, ...q };

    const wkRaw = pick(src, "wk", "workouts_list", "workout_list");
    const wk = wkRaw !== null ? parseWk(wkRaw) : null;

    const steps = toInt(pick(src, "steps"));
    const workouts = toInt(pick(src, "workouts", "gym")) ?? (wk ? wk.gym.length : null);
    const cals = toNum(pick(src, "calories", "cals", "energy"));
    const protein = toNum(pick(src, "protein"));
    const cardio = toNum(pick(src, "cardio_min", "cardio", "cardio_minutes", "cardiomin")) ?? (wk ? Math.round(wk.cardio.reduce((a, w) => a + w.min, 0)) : null);
    let date = String(pick(src, "date") ?? "").trim().toLowerCase();
    if (date === "yesterday" || date === "yday" || date === "-1") date = addDays(laDate(), -1);
    else if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) date = laDate();

    // --- WEEK LOCK ---
    const today = laDate();
    if (date > today) date = today; // no future dates
    const dow = new Date(today + "T12:00:00Z").getUTCDay(); // 1 = Monday
    const thisMonday = addDays(today, -((dow + 6) % 7));
    const cutoff = (dow === 1 && laHour() < 12) ? addDays(thisMonday, -7) : thisMonday;
    if (date < cutoff) return json({ ok: false, error: `week locked — ${date} is before ${cutoff}. Edits only count within the current week.` }, 422);

    if (steps === null && workouts === null && cals === null && protein === null && cardio === null) {
      return json({ ok: false, error: "need at least one of steps/calories/protein/workouts/cardio_min/wk" }, 400);
    }

    const [u] = await sql`select id, display_name from fitness.app_user where health_token = ${token} limit 1`;
    if (!u) return json({ ok: false, error: "unknown token" }, 401);

    const recorded = { steps, calories: cals, protein, workouts, cardio_min: cardio };
    if (q.dry === "1") return json({ ok: true, dry: true, user: u.display_name, date, would_record: recorded, classified: wk });

    const gymNames = wk && wk.gym.length ? wk.gym.map((w) => w.name) : ["phone health"];
    const cardioNames = wk && wk.cardio.length ? wk.cardio.map((w) => `${w.name} ${Math.round(w.min)}m`) : ["phone health"];
    const raw = sql.json({ source: "apple_health", via: wk ? "shortcut-wk" : "shortcut", ...(wk ? { wk } : {}) });

    if (steps !== null || workouts !== null) {
      await sql`insert into fitness.activity_log (user_id, log_date, steps, workouts, raw)
                values (${u.id}, ${date}, ${steps}, ${workouts}, ${raw})`;
    }
    if (cals !== null || protein !== null) {
      await sql`insert into fitness.daily_log (user_id, log_date, calories, protein_g, food_logged, raw)
                values (${u.id}, ${date}, ${cals ?? 0}, ${protein ?? 0}, ${(cals ?? 0) > 0}, ${raw})`;
    }
    if (workouts !== null) {
      await sql`insert into fitness.gym_log (user_id, log_date, sessions, names, raw)
                values (${u.id}, ${date}, ${workouts}, ${gymNames}, ${raw})`;
    }
    if (cardio !== null) {
      await sql`insert into fitness.cardio_log (user_id, log_date, minutes, names, raw)
                values (${u.id}, ${date}, ${cardio}, ${cardioNames}, ${raw})`;
    }

    return json({ ok: true, user: u.display_name, date, recorded, classified: wk });
  } catch (e) {
    return json({ ok: false, error: String(e instanceof Error ? e.message : e) }, 500);
  } finally {
    try { await sql.end(); } catch { }
  }
});
