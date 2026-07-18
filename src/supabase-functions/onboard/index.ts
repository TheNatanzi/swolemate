// onboard — per-friend onboarding hub backend. Gated by the user's private
// health_token (?u=...), no anon key needed. Powers the hosted onboard.html page.
//   GET  ?u=<token>&api=1  -> that friend's current profile (goals, whatsapp, gender, meal times, activity_metric)
//   POST { u, gender, calorie_goal, protein_goal, gym_goal, steps_goal, cardio_goal, activity_metric,
//          whatsapp, breakfast_time, lunch_time, dinner_time, skip_breakfast } -> save

import postgres from "https://deno.land/x/postgresjs@v3.4.5/mod.js";

const CORS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "content-type",
};
const json = (b: unknown, s = 200) => new Response(JSON.stringify(b), { status: s, headers: { ...CORS, "content-type": "application/json" } });
const num = (v: unknown) => { const n = parseInt(String(v ?? "").replace(/[^\d]/g, ""), 10); return Number.isFinite(n) ? n : null; };
const cleanPhone = (v: unknown) => { const d = String(v ?? "").replace(/[^\d]/g, ""); return d.length >= 10 ? d : null; };
const mt = (v: unknown) => { const s = String(v ?? "").trim(); return /^\d{2}:\d{2}$/.test(s) ? s : null; };

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  const url = new URL(req.url);
  let token = url.searchParams.get("u") ?? "";
  const sql = postgres(Deno.env.get("SUPABASE_DB_URL")!, { prepare: false });
  try {
    let body: any = null;
    if (req.method === "POST") { body = await req.json().catch(() => ({})); token = body.u || token; }
    if (!token) return json({ ok: false, error: "missing token" }, 400);

    const [u] = await sql`
      select au.id, au.display_name, au.pod_id, p.name as pod_name
      from fitness.app_user au join fitness.pod p on p.id = au.pod_id
      where au.health_token = ${token} limit 1`;
    if (!u) return json({ ok: false, error: "unknown link" }, 401);

    let saved = false;
    if (body) {
      const am = String(body.activity_metric ?? "").toLowerCase();
      if (am === "steps" || am === "cardio") { await sql`update fitness.app_user set activity_metric = ${am} where id = ${u.id}`; saved = true; }
      const cal = num(body.calorie_goal), prot = num(body.protein_goal), gym = num(body.gym_goal), steps = num(body.steps_goal), cardio = num(body.cardio_goal);
      if (cal !== null && prot !== null) {
        await sql`insert into fitness.user_goals (user_id, calorie_goal, protein_goal, gym_goal, steps_goal, cardio_goal)
                  values (${u.id}, ${cal}, ${prot}, ${gym}, ${steps}, ${cardio})`;
        saved = true;
      }
      const phone = cleanPhone(body.whatsapp);
      if (phone) { await sql`update fitness.app_user set whatsapp_to = ${phone} where id = ${u.id}`; saved = true; }
      const g = String(body.gender ?? "").toUpperCase();
      if (g === "M" || g === "F") { await sql`update fitness.app_user set gender = ${g} where id = ${u.id}`; saved = true; }
      if ("breakfast_time" in body || "lunch_time" in body || "dinner_time" in body || "skip_breakfast" in body) {
        const skipB = body.skip_breakfast === true || body.skip_breakfast === "true";
        await sql`update fitness.app_user set
                    breakfast_time = ${mt(body.breakfast_time)}, lunch_time = ${mt(body.lunch_time)},
                    dinner_time = ${mt(body.dinner_time)}, skip_breakfast = ${skipB}
                  where id = ${u.id}`;
        saved = true;
      }
    }

    const [g] = await sql`select calorie_goal, protein_goal, gym_goal, steps_goal, cardio_goal from fitness.v_user_goal_latest where user_id = ${u.id}`;
    const [au2] = await sql`select whatsapp_to, gender, activity_metric, breakfast_time, lunch_time, dinner_time, skip_breakfast from fitness.app_user where id = ${u.id}`;

    return json({
      ok: true, saved,
      display_name: u.display_name, pod_name: u.pod_name,
      calorie_goal: g?.calorie_goal ?? null, protein_goal: g?.protein_goal ?? null,
      gym_goal: g?.gym_goal ?? null, steps_goal: g?.steps_goal ?? null, cardio_goal: g?.cardio_goal ?? null,
      activity_metric: au2?.activity_metric ?? "steps",
      whatsapp_to: au2?.whatsapp_to ?? null, gender: au2?.gender ?? null,
      breakfast_time: au2?.breakfast_time ?? null, lunch_time: au2?.lunch_time ?? null,
      dinner_time: au2?.dinner_time ?? null, skip_breakfast: au2?.skip_breakfast ?? false,
    });
  } catch (e) {
    return json({ ok: false, error: String(e instanceof Error ? e.message : e) }, 500);
  } finally {
    try { await sql.end(); } catch { /* ignore */ }
  }
});
