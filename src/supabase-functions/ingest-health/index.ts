// ingest-health v6 — catches phone health data from a Shortcut, writes to the tables the coach reads.
// Accepts: steps, workouts/gym, calories, protein, cardio_min (cardio minutes for cardio-metric users).
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

    const steps = toInt(pick(src, "steps"));
    const workouts = toInt(pick(src, "workouts", "gym"));
    const cals = toNum(pick(src, "calories", "cals", "energy"));
    const protein = toNum(pick(src, "protein"));
    const cardio = toNum(pick(src, "cardio_min", "cardio", "cardio_minutes", "cardiomin"));
    let date = String(pick(src, "date") ?? "");
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) date = laDate();

    // --- WEEK LOCK ---
    const today = laDate();
    if (date > today) date = today; // no future dates
    const dow = new Date(today + "T12:00:00Z").getUTCDay(); // 1 = Monday
    const thisMonday = addDays(today, -((dow + 6) % 7));
    const cutoff = (dow === 1 && laHour() < 12) ? addDays(thisMonday, -7) : thisMonday;
    if (date < cutoff) return json({ ok: false, error: `week locked — ${date} is before ${cutoff}. Edits only count within the current week.` }, 422);

    if (steps === null && workouts === null && cals === null && protein === null && cardio === null) {
      return json({ ok: false, error: "need at least one of steps/calories/protein/workouts/cardio_min" }, 400);
    }

    const [u] = await sql`select id, display_name from fitness.app_user where health_token = ${token} limit 1`;
    if (!u) return json({ ok: false, error: "unknown token" }, 401);

    if (steps !== null || workouts !== null) {
      await sql`insert into fitness.activity_log (user_id, log_date, steps, workouts, raw)
                values (${u.id}, ${date}, ${steps}, ${workouts}, ${sql.json({ source: "apple_health", via: "shortcut" })})`;
    }
    if (cals !== null || protein !== null) {
      await sql`insert into fitness.daily_log (user_id, log_date, calories, protein_g, food_logged, raw)
                values (${u.id}, ${date}, ${cals ?? 0}, ${protein ?? 0}, ${(cals ?? 0) > 0}, ${sql.json({ source: "apple_health", via: "shortcut" })})`;
    }
    if (cardio !== null) {
      await sql`insert into fitness.cardio_log (user_id, log_date, minutes, names, raw)
                values (${u.id}, ${date}, ${cardio}, ${["phone health"]}, ${sql.json({ source: "apple_health", via: "shortcut" })})`;
    }

    return json({ ok: true, user: u.display_name, date, recorded: { steps, calories: cals, protein, workouts, cardio_min: cardio } });
  } catch (e) {
    return json({ ok: false, error: String(e instanceof Error ? e.message : e) }, 500);
  } finally {
    try { await sql.end(); } catch { }
  }
});
