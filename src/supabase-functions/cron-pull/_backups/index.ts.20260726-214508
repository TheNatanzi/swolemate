// cron-pull v17 — scrapes Cronometer for the squad and writes the tables the coach reads.
// v17: multi-account. Primary comes from CRONOMETER_EMAIL/PASSWORD env (full pull: food + gym + cardio).
//      Extra members live in fitness.cronometer_account (user_id, email, password, food_only).
//      food_only=true (default) pulls just calories/protein — their workouts come from Oura (cron-pull-oura),
//      so writing Cronometer exercises too would race in the v_*_latest views.
// Default pull window = the CURRENT week (Mon..today): edits heal within the week, past weeks are frozen.
// Grace: Monday before 12pm LA also re-pulls LAST week so Sunday-night logging lands before the noon recap.
import postgres from "https://deno.land/x/postgresjs@v3.4.5/mod.js";

const BASE = "https://cronometer.com";
const GWT_APP = `${BASE}/cronometer/app`;
const NOCACHE_JS = `${BASE}/cronometer/cronometer.nocache.js`;
const GWT_CONTENT_TYPE = "text/x-gwt-rpc; charset=UTF-8";
const GWT_MODULE_BASE = "https://cronometer.com/cronometer/";
const STRONGNAME = "2D6A926E3729946302DC68073CB0D550";
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36";

const GWT_AUTHENTICATE = `7|0|5|https://cronometer.com/cronometer/|${STRONGNAME}|com.cronometer.shared.rpc.CronometerService|authenticate|java.lang.Integer/3438268394|1|2|3|4|1|5|5|-300|`;
const genTokenBody = (nonce, userId) => `7|0|8|https://cronometer.com/cronometer/|${STRONGNAME}|com.cronometer.shared.rpc.CronometerService|generateAuthorizationToken|java.lang.String/2004016611|I|com.cronometer.shared.user.AuthScope/2065601159|${nonce}|1|2|3|4|4|5|6|6|7|8|${userId}|3600|7|2|`;

class Jar {
  m = new Map();
  update(res) { const list = res.headers.getSetCookie?.() ?? []; for (const c of list) { const pair = c.split(";")[0]; const i = pair.indexOf("="); if (i > 0) this.m.set(pair.slice(0, i).trim(), pair.slice(i + 1).trim()); } }
  get(n) { return this.m.get(n); }
  header() { return [...this.m].map(([k, v]) => `${k}=${v}`).join("; "); }
}
function splitCsv(line) { const out = []; let cur = "", q = false; for (let i = 0; i < line.length; i++) { const ch = line[i]; if (q) { if (ch === '"' && line[i + 1] === '"') { cur += '"'; i++; } else if (ch === '"') q = false; else cur += ch; } else { if (ch === '"') q = true; else if (ch === ",") { out.push(cur); cur = ""; } else cur += ch; } } out.push(cur); return out; }
function rows(csv) { const lines = csv.trim().split(/\r?\n/); if (lines.length < 2) return []; const headers = splitCsv(lines[0]).map((h) => h.trim()); return lines.slice(1).map((l) => { const c = splitCsv(l); return Object.fromEntries(headers.map((h, i) => [h, (c[i] ?? "").trim()])); }); }

async function login(email, password) {
  const jar = new Jar(); const base = { "user-agent": UA };
  let res = await fetch(`${BASE}/login/`, { headers: base }); jar.update(res);
  const anticsrf = (await res.text()).match(/name="anticsrf"\s+value="([^"]+)"/)?.[1];
  if (!anticsrf) throw new Error("anticsrf token not found (site changed?)");
  res = await fetch(`${BASE}/login`, { method: "POST", headers: { ...base, "content-type": "application/x-www-form-urlencoded", cookie: jar.header() }, body: new URLSearchParams({ username: email, password, anticsrf }).toString() }); jar.update(res);
  const sesnonce = jar.get("sesnonce");
  if (!sesnonce) throw new Error("Login failed — check email/password and that 2-factor is OFF.");
  const permutation = [...new Set((await (await fetch(NOCACHE_JS, { headers: base })).text()).match(/[0-9A-F]{32}/g) ?? [])][0];
  if (!permutation) throw new Error("Could not read GWT permutation");
  const gwtHeaders = () => ({ ...base, "content-type": GWT_CONTENT_TYPE, "x-gwt-module-base": GWT_MODULE_BASE, "x-gwt-permutation": permutation, cookie: jar.header() });
  res = await fetch(GWT_APP, { method: "POST", headers: gwtHeaders(), body: GWT_AUTHENTICATE }); jar.update(res);
  const userId = (await res.text()).match(/OK\[(\d+),/)?.[1];
  if (!userId) throw new Error("authenticate returned no userId");
  return { jar, base, gwtHeaders, userId };
}
async function exportCsv(s, generate, start, end) {
  const nonce = s.jar.get("sesnonce");
  const res0 = await fetch(GWT_APP, { method: "POST", headers: s.gwtHeaders(), body: genTokenBody(nonce, s.userId) });
  const token = (await res0.text()).match(/"([^"]+)"/)?.[1];
  if (!token) throw new Error("no export token");
  const url = `${BASE}/export?nonce=${encodeURIComponent(token)}&generate=${generate}&start=${start}&end=${end}`;
  const res = await fetch(url, { headers: { ...s.base, cookie: s.jar.header(), "sec-fetch-dest": "document", "sec-fetch-mode": "navigate", "sec-fetch-site": "same-origin" } });
  return await res.text();
}

function parseDaily(csv) { const out = []; for (const r of rows(csv)) { const date = r["Date"]; if (!date) continue; const calories = parseFloat(r["Energy (kcal)"]) || 0; const protein = parseFloat(r["Protein (g)"]) || 0; out.push({ log_date: date, calories, protein_g: protein, food_logged: calories > 0, raw: r }); } return out; }
function isRealWorkout(name, minutes) { const n = (name || "").trim(); if (!n) return false; if (/fitbit activity/i.test(n)) return false; if (/^other\b/i.test(n)) return false; if (/\bwalk/i.test(n)) return false; /* walking = cardio, never a gym session */ if (minutes > 240) return false; return true; }
function parseGym(csv) { const byDay = {}; for (const r of rows(csv)) { const day = r["Day"]; const name = r["Exercise"]; const minutes = parseFloat(r["Minutes"]) || 0; if (!day || !isRealWorkout(name, minutes)) continue; (byDay[day] ??= { sessions: 0, minutes: 0, names: [], raw: [] }); byDay[day].sessions++; byDay[day].minutes += minutes; byDay[day].names.push(name); byDay[day].raw.push(r); } return byDay; }

// --- Cardio: sum minutes of cardio-type workouts (treadmill/run/bike/row/stair/elliptical/swim/HIIT/etc). ---
const CARDIO_RE = /(treadmill|running|\brun\b|jog|\bwalk|elliptical|cross[- ]?trainer|arc trainer|stair|stepper|step ?mill|rowing|\brow\b|\berg\b|cycling|\bbike|bicycl|spin(?:ning)?|\bswim|cardio|aerobic|hiit|high intensity interval|jump ?rope|skipping|sprint|conditioning)/i;
function isCardio(name, group, minutes) {
  const n = (name || "").trim();
  if (!n) return false;
  if (/fitbit activity/i.test(n)) return false;
  if (minutes > 240) return false; // all-day auto-sync noise
  if (/cardio|aerobic/i.test(group || "")) return true;
  return CARDIO_RE.test(n);
}
function parseCardio(csv) { const byDay = {}; for (const r of rows(csv)) { const day = r["Day"]; const name = r["Exercise"]; const group = r["Group"]; const minutes = parseFloat(r["Minutes"]) || 0; if (!day || !isCardio(name, group, minutes)) continue; (byDay[day] ??= { minutes: 0, names: [], raw: [] }); byDay[day].minutes += minutes; byDay[day].names.push(name); byDay[day].raw.push(r); } return byDay; }

function laDate(offsetDays = 0) { const d = new Date(Date.now() + offsetDays * 86400000); return new Intl.DateTimeFormat("en-CA", { timeZone: "America/Los_Angeles" }).format(d); }
const addDays = (s, n) => { const d = new Date(s + "T12:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
const laHour = () => parseInt(new Intl.DateTimeFormat("en-US", { timeZone: "America/Los_Angeles", hour12: false, hour: "2-digit" }).format(new Date()), 10);
function weekWindowStart() {
  const today = laDate(0);
  const dow = new Date(today + "T12:00:00Z").getUTCDay(); // 1 = Monday
  const thisMonday = addDays(today, -((dow + 6) % 7));
  return (dow === 1 && laHour() < 12) ? addDays(thisMonday, -7) : thisMonday;
}

async function pullAccount(sql, acct, start, end, dryRun) {
  const s = await login(acct.email, acct.password);
  const dailyCsv = await exportCsv(s, "dailySummary", start, end);
  // --- CANARY SHAPE CHECK (distinguishes "didn't log" from "scraper broke") ---
  if (!/Energy \(kcal\)/i.test(dailyCsv)) {
    throw new Error(`SCRAPE_BREAK[${acct.name}]: dailySummary export malformed — no 'Energy (kcal)' column (login expired or Cronometer changed). First 120 chars: ` + dailyCsv.slice(0, 120).replace(/\s+/g, " "));
  }
  const days = parseDaily(dailyCsv);
  let gym = {}, cardio = {};
  if (!acct.food_only) {
    const exerciseCsv = await exportCsv(s, "exercises", start, end);
    gym = parseGym(exerciseCsv);
    cardio = parseCardio(exerciseCsv);
  }
  let food = 0, gymRows = 0, cardioRows = 0;
  if (!dryRun) {
    for (const d of days) { await sql`insert into fitness.daily_log (user_id, log_date, calories, protein_g, food_logged, raw) values (${acct.user_id}, ${d.log_date}, ${d.calories}, ${d.protein_g}, ${d.food_logged}, ${sql.json(d.raw)})`; food++; }
    for (const [day, g] of Object.entries(gym)) { await sql`insert into fitness.gym_log (user_id, log_date, sessions, minutes, names, raw) values (${acct.user_id}, ${day}, ${g.sessions}, ${g.minutes}, ${g.names}, ${sql.json(g.raw)})`; gymRows++; }
    for (const [day, c] of Object.entries(cardio)) { await sql`insert into fitness.cardio_log (user_id, log_date, minutes, names, raw) values (${acct.user_id}, ${day}, ${c.minutes}, ${c.names}, ${sql.json(c.raw)})`; cardioRows++; }
  }
  return {
    account: acct.name, food_only: acct.food_only,
    food_days: days.map((d) => ({ log_date: d.log_date, calories: d.calories, protein_g: d.protein_g })),
    gym_days: Object.entries(gym).map(([day, g]) => ({ log_date: day, sessions: g.sessions, names: g.names })),
    cardio_days: Object.entries(cardio).map(([day, c]) => ({ log_date: day, minutes: c.minutes, names: c.names })),
    rows_written: { food, gym: gymRows, cardio: cardioRows },
  };
}

Deno.serve(async (req) => {
  const url = new URL(req.url);
  const start = url.searchParams.get("start") ?? weekWindowStart();
  const end = url.searchParams.get("end") ?? laDate(0);
  const dryRun = url.searchParams.get("dry") === "1";
  const only = url.searchParams.get("only"); // limit to one account by name (debug)
  const sql = postgres(Deno.env.get("SUPABASE_DB_URL"), { prepare: false });
  try {
    const email = Deno.env.get("CRONOMETER_EMAIL");
    const password = Deno.env.get("CRONOMETER_PASSWORD");
    if (!email || !password) throw new Error("Missing CRONOMETER_EMAIL / CRONOMETER_PASSWORD secrets");
    const [pu] = await sql`select id from fitness.app_user where cronometer_ref = 'primary' limit 1`;
    if (!pu) throw new Error("No primary app_user found");

    const gen = url.searchParams.get("gen");
    if (gen) { const s = await login(email, password); return Response.json({ ok: true, generate: gen, csv: await exportCsv(s, gen, start, end) }); }

    const extra = await sql`select ca.user_id, ca.email, ca.password, ca.food_only, au.display_name from fitness.cronometer_account ca join fitness.app_user au on au.id = ca.user_id where ca.user_id <> ${pu.id}`;
    const accounts = [
      { user_id: pu.id, email, password, food_only: false, name: "primary" },
      ...extra.map((r) => ({ user_id: r.user_id, email: r.email, password: r.password, food_only: r.food_only, name: r.display_name })),
    ].filter((a) => !only || a.name.toLowerCase() === only.toLowerCase());

    const results = [], errors = [];
    for (const acct of accounts) {
      try { results.push(await pullAccount(sql, acct, start, end, dryRun)); }
      catch (e) { errors.push(`${acct.name}: ${String(e instanceof Error ? e.message : e)}`); }
    }
    if (!dryRun) await sql`insert into fitness.health_check (ok, error) values (${errors.length === 0}, ${errors.length ? errors.join(" | ") : null})`;
    return Response.json({ ok: errors.length === 0, range: { start, end }, results, errors: errors.length ? errors : undefined });
  } catch (e) {
    const msg = String(e instanceof Error ? e.message : e);
    try { await sql`insert into fitness.health_check (ok, error) values (false, ${msg})`; } catch { /* ignore */ }
    return Response.json({ ok: false, error: msg }, { status: 500 });
  } finally {
    try { await sql.end(); } catch { /* ignore */ }
  }
});
