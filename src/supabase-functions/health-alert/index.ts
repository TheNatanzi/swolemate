// health-alert — watchdog that DMs Medi (via the same AutoRemote pipe the coach uses)
// when the data pipeline breaks. Isolated: reads state + pushes a message; never touches
// the data-pulling jobs. Scheduled by pg_cron every ~30 min.
//   ?test=1 -> sends one live test ping and returns (no detection).
// Delivery tag comes from fitness.app_config 'alert_tag' (default 'SM_ALERT=:=') so the
// phone's Tasker can route alerts to Medi privately, separate from the group's 'swole=:=' feed.
import postgres from "https://deno.land/x/postgresjs@v3.4.5/mod.js";

const AR = "https://autoremotejoaomgcd.appspot.com/sendmessage";

async function setCfg(sql, k, v) {
  await sql`update fitness.app_config set value = ${v} where key = ${k}`;
  await sql`insert into fitness.app_config (key, value) select ${k}, ${v} where not exists (select 1 from fitness.app_config where key = ${k})`;
}

Deno.serve(async (req) => {
  const q = new URL(req.url).searchParams;
  const sql = postgres(Deno.env.get("SUPABASE_DB_URL"), { prepare: false });
  try {
    const [ar] = await sql`select value from fitness.app_config where key = 'autoremote_key'`;
    const key = ar?.value;
    if (!key) return Response.json({ ok: false, error: "no autoremote_key in app_config" });
    const [tg] = await sql`select value from fitness.app_config where key = 'alert_tag'`;
    const tag = tg?.value || "SM_ALERT=:=";
    const push = async (text) => {
      try { const r = await fetch(`${AR}?key=${encodeURIComponent(key)}&message=${encodeURIComponent(tag + text)}`); return r.ok; }
      catch { return false; }
    };

    if (q.get("test") === "1") {
      const ok = await push("🚨 SwoleMate alerts are LIVE — test ping. If this reached you privately, you're all set. ✅");
      return Response.json({ ok, test: true, tag });
    }

    const problems = [];

    // (1) Cronometer / data-pull failures logged since we last checked
    const [st] = await sql`select value from fitness.app_config where key = 'alert_last_check'`;
    const since = st?.value || new Date(Date.now() - 6 * 3600 * 1000).toISOString();
    const fails = await sql`select checked_at, error from fitness.health_check where ok = false and checked_at > ${since}::timestamptz order by checked_at desc limit 5`;
    for (const f of fails) problems.push({ k: `pull:${new Date(f.checked_at).getTime()}`, msg: `❌ Data pull failed: ${String(f.error ?? "").slice(0, 200)}` });

    // (2) Oura tokens that are expired (auto-refresh is failing)
    const expired = await sql`select au.display_name as n from fitness.oura_token ot join fitness.app_user au on au.id = ot.user_id where ot.expires_at < now()`;
    for (const e of expired) problems.push({ k: `oura:${e.n}`, msg: `❌ ${e.n}'s Oura token expired — auto-refresh is failing, their Oura data has stopped.` });

    // (3) A connected friend with no fresh data in >26h
    const stale = await sql`
      with connected as (
        select au.id, au.display_name as n from fitness.app_user au
        where exists (select 1 from fitness.oura_token o where o.user_id = au.id)
           or exists (select 1 from fitness.cronometer_account c where c.user_id = au.id)
      )
      select c.n, greatest(
        coalesce((select max(pulled_at) from fitness.activity_log a where a.user_id = c.id), 'epoch'::timestamptz),
        coalesce((select max(pulled_at) from fitness.daily_log d where d.user_id = c.id), 'epoch'::timestamptz)
      ) as last_push
      from connected c`;
    for (const s of stale) {
      const last = s.last_push ? new Date(s.last_push).getTime() : 0;
      if (Date.now() - last > 26 * 3600 * 1000) problems.push({ k: `stale:${s.n}`, msg: `⚠️ No new data from ${s.n} in 26h+ — check their phone/shortcut or connection.` });
    }

    // Dedup: only alert on problems not already active; clear resolved ones.
    const [ak] = await sql`select value from fitness.app_config where key = 'alert_active'`;
    let active = [];
    try { active = JSON.parse(ak?.value || "[]"); } catch { active = []; }
    const activeSet = new Set(active);
    const curKeys = problems.map((p) => p.k);
    const fresh = problems.filter((p) => !activeSet.has(p.k));

    let sent = false;
    if (fresh.length) sent = await push("🚨 SwoleMate health alert\n\n" + fresh.map((p) => p.msg).join("\n\n"));

    await setCfg(sql, "alert_active", JSON.stringify(curKeys));
    await setCfg(sql, "alert_last_check", new Date().toISOString());

    return Response.json({ ok: true, problems: problems.map((p) => p.msg), alerted: fresh.length, sent });
  } catch (e) {
    return Response.json({ ok: false, error: String(e instanceof Error ? e.message : e) }, { status: 500 });
  } finally {
    try { await sql.end(); } catch { /* ignore */ }
  }
});
