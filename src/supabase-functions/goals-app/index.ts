// goals-app v9 — preferences API + fallback HTML form.
import postgres from "https://deno.land/x/postgresjs@v3.4.5/mod.js";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
};
const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { ...CORS, "content-type": "application/json" } });
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function page(body) {
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Fitness goals</title><style>
  :root { color-scheme: light dark; } * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; background: #0b141a; color: #e9edef; }
  .wrap { max-width: 460px; margin: 0 auto; padding: 24px 18px 60px; }
  h1 { font-size: 22px; font-weight: 600; margin: 12px 0 4px; }
  .sub { color: #8696a0; font-size: 14px; margin: 0 0 22px; }
  .card { background: #111b21; border: 1px solid #22303a; border-radius: 14px; padding: 18px; margin-bottom: 16px; }
  label { display: block; font-size: 14px; color: #8696a0; margin: 14px 0 6px; }
  input { width: 100%; font-size: 17px; padding: 12px 14px; border-radius: 10px; border: 1px solid #2a3942; background: #202c33; color: #e9edef; }
  input:focus { outline: none; border-color: #00a884; }
  button { width: 100%; margin-top: 22px; font-size: 16px; font-weight: 600; padding: 14px; border: none; border-radius: 10px; background: #00a884; color: #0b141a; cursor: pointer; }
  .ok { background: #0b3d2e; border: 1px solid #00a884; color: #b9f5d8; padding: 12px 14px; border-radius: 10px; margin-bottom: 16px; font-size: 14px; }
  .row { display: flex; gap: 12px; } .row > div { flex: 1; }
  .hint { font-size: 12px; color: #667781; margin-top: 4px; }
</style></head><body><div class="wrap">${body}</div></body></html>`;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  const url = new URL(req.url);
  const api = url.searchParams.get("api") === "1" || (req.headers.get("content-type") || "").includes("application/json");
  const sql = postgres(Deno.env.get("SUPABASE_DB_URL"), { prepare: false });
  try {
    const cfg = await sql`select value from fitness.app_config where key = 'goals_token'`;
    const goodToken = cfg[0]?.value;

    let token = url.searchParams.get("token") ?? "";
    let form = null;
    let jbody = null;
    if (req.method === "POST") {
      if ((req.headers.get("content-type") || "").includes("application/json")) { jbody = await req.json().catch(() => ({})); token = jbody.token || token; }
      else { form = await req.formData(); token = String(form.get("token") || token); }
    }
    if (!goodToken || token !== goodToken) {
      return api ? json({ ok: false, error: "unauthorized" }, 401)
        : new Response(page(`<h1>Not authorized</h1><p class="sub">This link is missing its access code.</p>`), { status: 401, headers: { "content-type": "text/html; charset=utf-8" } });
    }

    const [u] = await sql`select u.id as user_id, u.display_name, u.pod_id, p.name as pod_name from fitness.app_user u join fitness.pod p on p.id = u.pod_id where u.cronometer_ref = 'primary' limit 1`;
    if (!u) throw new Error("No user found");

    let saved = false;
    const src = jbody ?? (form ? Object.fromEntries([...form.entries()]) : null);
    if (src) {
      const num = (v) => { const n = parseInt(String(v ?? ""), 10); return Number.isFinite(n) ? n : null; };
      const cal = num(src.calorie_goal), prot = num(src.protein_goal), gym = num(src.gym_goal), steps = num(src.steps_goal);
      if (cal !== null && prot !== null) {
        await sql`insert into fitness.user_goals (user_id, calorie_goal, protein_goal, gym_goal, steps_goal)
                  values (${u.user_id}, ${cal}, ${prot}, ${gym}, ${steps})`;
        saved = true;
      }
      const stime = String(src.send_time ?? "").trim();
      if (/^\d{2}:\d{2}$/.test(stime)) { await sql`update fitness.pod set send_time = ${stime + ":00"} where id = ${u.pod_id}`; saved = true; }
    }

    const [g] = await sql`select calorie_goal, protein_goal, gym_goal, steps_goal from fitness.v_user_goal_latest where user_id = ${u.user_id}`;
    const [p] = await sql`select to_char(send_time,'HH24:MI') as t from fitness.pod where id = ${u.pod_id}`;

    if (api) {
      return json({
        ok: true, saved, display_name: u.display_name, pod_name: u.pod_name,
        calorie_goal: g?.calorie_goal ?? null, protein_goal: g?.protein_goal ?? null,
        gym_goal: g?.gym_goal ?? null, steps_goal: g?.steps_goal ?? null, send_time: p?.t ?? null,
      });
    }

    const okMsg = saved ? `<div class="ok">Saved. Your coach will use these from the next message on.</div>` : "";
    const body = `${okMsg}<h1>Your fitness goals</h1><p class="sub">${esc(u.display_name)} · ${esc(u.pod_name)}</p>
      <form method="POST" action="?token=${esc(token)}"><input type="hidden" name="token" value="${esc(token)}">
        <div class="card"><div class="row">
          <div><label>Daily calories</label><input name="calorie_goal" type="number" inputmode="numeric" value="${esc(g?.calorie_goal ?? "")}" required></div>
          <div><label>Daily protein (g)</label><input name="protein_goal" type="number" inputmode="numeric" value="${esc(g?.protein_goal ?? "")}" required></div>
        </div></div>
        <div class="card"><div class="row">
          <div><label>Gym / week</label><input name="gym_goal" type="number" inputmode="numeric" value="${esc(g?.gym_goal ?? "")}"></div>
          <div><label>Steps / day</label><input name="steps_goal" type="number" inputmode="numeric" value="${esc(g?.steps_goal ?? "")}"></div>
        </div></div>
        <div class="card"><label>Daily message time (leader sets this for the group)</label><input name="send_time" type="time" value="${esc(p?.t ?? "08:00")}"><div class="hint">Your local time. Sent every day at this time.</div></div>
        <button type="submit">Save my goals</button>
      </form>`;
    return new Response(page(body), { headers: { "content-type": "text/html; charset=utf-8" } });
  } catch (e) {
    const msg = String(e instanceof Error ? e.message : e);
    return api ? json({ ok: false, error: msg }, 500)
      : new Response(page(`<h1>Something went wrong</h1><p class="sub">${esc(msg)}</p>`), { status: 500, headers: { "content-type": "text/html; charset=utf-8" } });
  } finally {
    try { await sql.end(); } catch { }
  }
});
