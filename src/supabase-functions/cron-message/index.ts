import postgres from "https://deno.land/x/postgresjs@v3.4.5/mod.js";

function stepsStr(s) { return `${s.avgSteps.toLocaleString()}${s.stepsGoal ? ` of ${s.stepsGoal.toLocaleString()} goal` : ""}`; }

function composeMessage(s) {
  const cal = s.goalCal ? `${s.avgCal} cal (goal ${s.goalCal})` : `${s.avgCal} cal`;
  const prot = s.goalProt ? `${s.avgProt}g protein (goal ${s.goalProt})` : `${s.avgProt}g protein`;
  let line;
  if (s.loggedDays <= 3) line = "Let's log more this week — consistency first. You've got this 💪";
  else if (s.goalProt && s.avgProt < s.goalProt * 0.9) line = "Solid logging! Nudge that protein up a bit today 🥩";
  else line = "Crushing it — keep the streak going 🔥";
  return [`Morning ${s.name}! 🌅 Your weekly check-in:`, `• Gym: ${s.gymSessions} of ${s.gymGoal ?? "?"} sessions 🏋️`, `• Steps (7-day avg): ${stepsStr(s)} 👟`, `• Food logged: ${s.loggedDays} of the last 7 days`, `• On logged days: ${cal} · ${prot}`, ``, line].join("\n");
}

async function statsForUser(sql, userId) {
  const rows = await sql`select log_date, calories, protein_g, food_logged from fitness.v_daily_latest where user_id = ${userId} and log_date >= (current_date - 6) order by log_date`;
  const logged = rows.filter((r) => r.food_logged);
  const n = logged.length || 0;
  const avg = (arr, key) => n ? Math.round(arr.reduce((a, r) => a + Number(r[key] || 0), 0) / n) : 0;
  const [goal] = await sql`select calorie_goal, protein_goal, gym_goal, steps_goal from fitness.v_user_goal_latest where user_id = ${userId}`;
  const [act] = await sql`select coalesce(round(avg(steps)), 0)::int as avg_steps from fitness.v_activity_latest where user_id = ${userId} and log_date >= (current_date - 6) and steps is not null`;
  const [gym] = await sql`select coalesce(sum(sessions), 0)::int as gym_sessions from fitness.v_gym_latest where user_id = ${userId} and log_date >= (current_date - 6)`;
  return { loggedDays: n, avgCal: avg(logged, "calories"), avgProt: avg(logged, "protein_g"), goalCal: goal?.calorie_goal ?? null, goalProt: goal?.protein_goal ?? null, gymGoal: goal?.gym_goal ?? null, stepsGoal: goal?.steps_goal ?? null, avgSteps: act?.avg_steps ?? 0, gymSessions: gym?.gym_sessions ?? 0 };
}

async function waPost(payload) {
  const phoneId = Deno.env.get("WHATSAPP_PHONE_NUMBER_ID");
  const token = Deno.env.get("WHATSAPP_ACCESS_TOKEN");
  if (!phoneId || !token) return { sent: false, reason: "WhatsApp not configured yet" };
  const res = await fetch(`https://graph.facebook.com/v23.0/${phoneId}/messages`, { method: "POST", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }, body: JSON.stringify({ messaging_product: "whatsapp", ...payload }) });
  const body = await res.json().catch(() => ({}));
  return { sent: res.ok, status: res.status, id: body?.messages?.[0]?.id, body };
}
const sendWhatsApp = (to, text) => waPost({ to, type: "text", text: { body: text } });
const sendTemplate = (to, name, lang = "en_US") => waPost({ to, type: "template", template: { name, language: { code: lang } } });

// daily_checkin_v3: {{1}}name {{2}}gym {{3}}gymGoal {{4}}steps(+goal) {{5}}loggedDays {{6}}cal {{7}}goalCal {{8}}prot {{9}}goalProt {{10}}line
function sendDailyTemplate(to, s) {
  const p = (t) => ({ type: "text", text: String(t) });
  return waPost({ to, type: "template", template: { name: "daily_checkin_v3", language: { code: "en_US" }, components: [{ type: "body", parameters: [p(s.name), p(s.gymSessions), p(s.gymGoal ?? "-"), p(stepsStr(s)), p(s.loggedDays), p(s.avgCal), p(s.goalCal ?? "-"), p(s.avgProt), p(s.goalProt ?? "-"), p(s.line)] }] } });
}
function nudgeLine(s) {
  if (s.loggedDays <= 3) return "Let's log more this week - consistency first. You've got this.";
  if (s.goalProt && s.avgProt < s.goalProt * 0.9) return "Solid logging! Nudge that protein up a bit today.";
  return "Crushing it - keep the streak going.";
}

const WABA_ID = "1417420403770776";
async function createDailyTemplate() {
  const token = Deno.env.get("WHATSAPP_ACCESS_TOKEN");
  const body = { name: "daily_checkin_v3", language: "en_US", category: "UTILITY", components: [{ type: "BODY", text: "Morning {{1}}! Your weekly check-in. Gym: {{2}} of {{3}} sessions. Steps 7-day avg: {{4}}. Food logged {{5}} of the last 7 days. On logged days: {{6}} cal (goal {{7}}), {{8}}g protein (goal {{9}}). {{10}} - Coach", example: { body_text: [["Medi", "1", "3", "6,876 of 10,000 goal", "1", "2192", "2300", "211", "200", "Crushing it - keep the streak going."]] } }] };
  const res = await fetch(`https://graph.facebook.com/v23.0/${WABA_ID}/message_templates`, { method: "POST", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }, body: JSON.stringify(body) });
  return { status: res.status, body: await res.json().catch(() => ({})) };
}

Deno.serve(async (req) => {
  const url = new URL(req.url);
  const preview = url.searchParams.get("preview") === "1";
  const test = url.searchParams.get("test");
  const admin = url.searchParams.get("admin");
  const sql = postgres(Deno.env.get("SUPABASE_DB_URL"), { prepare: false });
  try {
    if (admin === "create_template") return Response.json(await createDailyTemplate());
    if (test) {
      const [u] = await sql`select u.id, u.display_name, u.whatsapp_to, u.pod_id from fitness.app_user u where u.cronometer_ref = 'primary' limit 1`;
      if (!u?.whatsapp_to) throw new Error("Primary user has no whatsapp_to set");
      let send, label;
      if (test === "template") { label = "hello_world"; send = await sendTemplate(u.whatsapp_to, "hello_world"); }
      else if (test === "daily") { label = "daily_checkin_v3"; const s = await statsForUser(sql, u.id); send = await sendDailyTemplate(u.whatsapp_to, { name: u.display_name, ...s, line: nudgeLine(s) }); }
      else { label = "phase1_text_test"; const s = await statsForUser(sql, u.id); send = await sendWhatsApp(u.whatsapp_to, composeMessage({ name: u.display_name, ...s })); }
      await sql`insert into fitness.message_log (pod_id, template, vars, wa_message_id, ok) values (${u.pod_id}, ${label}, ${sql.json({ test: true })}, ${send.id ?? null}, ${send.sent})`;
      return Response.json({ ok: send.sent, mode: label, api: send });
    }
    if (preview) {
      const [u] = await sql`select u.id, u.display_name, u.whatsapp_to, p.name as pod_name, p.send_time, p.timezone from fitness.app_user u join fitness.pod p on p.id = u.pod_id where u.cronometer_ref = 'primary' limit 1`;
      if (!u) throw new Error("No primary user found");
      const s = await statsForUser(sql, u.id);
      return Response.json({ ok: true, preview: true, pod: u.pod_name, send_time: u.send_time, timezone: u.timezone, stats: s, message: composeMessage({ name: u.display_name, ...s }) });
    }
    const pods = await sql`select p.id, p.name, p.send_time, p.timezone, p.whatsapp_group_id, u.id as leader_id, u.display_name, u.whatsapp_to from fitness.pod p join fitness.app_user u on u.id = p.leader_user_id`;
    const results = [];
    for (const p of pods) {
      const now = new Date();
      const hhmm = new Intl.DateTimeFormat("en-GB", { timeZone: p.timezone, hour: "2-digit", minute: "2-digit", hour12: false }).format(now);
      const [ph, pm] = String(p.send_time).split(":").map(Number);
      const [nh, nm] = hhmm.split(":").map(Number);
      const dueNow = nh === ph && Math.abs(nm - pm) < 15;
      if (!dueNow) { results.push({ pod: p.name, skipped: "not due", localTime: hhmm }); continue; }
      const dateStr = new Intl.DateTimeFormat("en-CA", { timeZone: p.timezone }).format(now);
      const already = await sql`select 1 from fitness.message_log where pod_id = ${p.id} and sent_at::date = ${dateStr}::date and ok = true limit 1`;
      if (already.length) { results.push({ pod: p.name, skipped: "already sent today" }); continue; }
      const s = await statsForUser(sql, p.leader_id);
      const hc = await sql`select ok from fitness.health_check where ok = true and checked_at > now() - interval '8 hours' limit 1`;
      const line = hc.length ? nudgeLine(s) : "Heads up: I could not reach Cronometer recently, so these numbers may be stale.";
      const to = p.whatsapp_group_id ?? p.whatsapp_to;
      const send = to ? await sendDailyTemplate(to, { name: p.display_name, ...s, line }) : { sent: false, reason: "no recipient number set" };
      await sql`insert into fitness.message_log (pod_id, template, vars, wa_message_id, ok) values (${p.id}, 'daily_checkin_v3', ${sql.json(s)}, ${send.id ?? null}, ${send.sent})`;
      results.push({ pod: p.name, sent: send.sent, reason: send.reason ?? null });
    }
    return Response.json({ ok: true, results });
  } catch (e) {
    return Response.json({ ok: false, error: String(e instanceof Error ? e.message : e) }, { status: 500 });
  } finally {
    try { await sql.end(); } catch { /* ignore */ }
  }
});
