// connect v3 — self-serve page for squad members to hook up their data sources.
// GET  ?u=<health_token>          -> page with live connection status, toddler-level directions,
//                                    (A) Oura connect button, (B) Cronometer login form.
// GET  ?u=<health_token>&api=1    -> JSON status {ok, name, oura, cron, oura_url} for the static connect.html page.
// POST {u, email, password}       -> verifies the Cronometer login actually works, then stores it in
//                                    fitness.cronometer_account (food_only=true; workouts come from Oura).
import postgres from "https://deno.land/x/postgresjs@v3.4.5/mod.js";

const OURA_START = "https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/oura-oauth";
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type",
};
const json = (b, s = 200) => new Response(JSON.stringify(b), { status: s, headers: { ...CORS, "content-type": "application/json" } });

// Lightweight Cronometer login check: real form login, pass = sesnonce cookie issued.
async function cronometerLoginWorks(email, password) {
  const jar = new Map();
  const grab = (res) => { for (const c of res.headers.getSetCookie?.() ?? []) { const p = c.split(";")[0]; const i = p.indexOf("="); if (i > 0) jar.set(p.slice(0, i).trim(), p.slice(i + 1).trim()); } };
  let res = await fetch("https://cronometer.com/login/", { headers: { "user-agent": UA } }); grab(res);
  const anticsrf = (await res.text()).match(/name="anticsrf"\s+value="([^"]+)"/)?.[1];
  if (!anticsrf) throw new Error("Cronometer site changed — tell Medi");
  const cookie = [...jar].map(([k, v]) => `${k}=${v}`).join("; ");
  res = await fetch("https://cronometer.com/login", { method: "POST", headers: { "user-agent": UA, "content-type": "application/x-www-form-urlencoded", cookie }, body: new URLSearchParams({ username: email, password, anticsrf }).toString() }); grab(res);
  return jar.has("sesnonce");
}

const page = (name, ouraUrl, st) => `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SwoleMate · connect</title><style>
:root{--bg:#0b0910;--panel:#15111d;--panel2:#1d1729;--line:#2b2340;--ink:#f4eefb;--muted:#a595bd;--dim:#6f6388;--green:#00d68f;--greenink:#04160f;--pink:#ff2e88;--gold:#f0b429}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;line-height:1.5;background-image:radial-gradient(700px 340px at 85% -8%,rgba(255,46,136,.15),transparent 60%),radial-gradient(600px 340px at 0% 0%,rgba(0,214,143,.10),transparent 55%)}
.wrap{max-width:480px;margin:0 auto;padding:28px 18px 70px}
.brand{font-weight:900;font-size:15px;text-transform:uppercase}.brand .p{color:var(--pink)}.brand .g{color:var(--green)}
h1{font-size:26px;font-weight:800;margin:14px 0 2px}.sub{color:var(--muted);font-size:14px;margin:0 0 16px}
h2{font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--dim);margin:26px 0 10px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:16px;margin-bottom:12px}
.chips{display:flex;gap:8px;margin-bottom:6px}
.chip{flex:1;text-align:center;font-size:13px;font-weight:800;padding:9px 6px;border-radius:999px;border:1px solid var(--line);background:var(--panel);color:var(--dim)}
.chip.on{border-color:var(--green);color:#b9f5d8;background:#05301f}
.step{display:flex;gap:10px;margin:9px 0;font-size:14.5px;color:var(--muted);line-height:1.5;align-items:flex-start}
.step .sn{flex:0 0 24px;height:24px;border-radius:50%;background:var(--panel2);border:1px solid var(--line);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:12px;color:var(--green)}
.step b{color:var(--ink)}
label{display:block;font-size:13px;color:var(--muted);margin:2px 0 7px;font-weight:600}
input{width:100%;font-size:17px;padding:12px 14px;border-radius:11px;border:1px solid #2f2645;background:var(--panel2);color:var(--ink)}
input:focus{outline:none;border-color:var(--green)}
.btn{display:block;width:100%;text-align:center;margin-top:14px;font-size:16px;font-weight:800;padding:15px;border:none;border-radius:12px;background:var(--green);color:var(--greenink);cursor:pointer;text-decoration:none}
.btn:disabled{opacity:.5}
.done{border-color:var(--green)}
.hint{font-size:12px;color:var(--dim);margin-top:8px}
.warn{font-size:12.5px;color:var(--gold);margin-top:8px}
.msg{padding:12px 14px;border-radius:11px;margin-top:12px;font-size:14px;display:none}
.msg.ok{display:block;background:#05301f;border:1px solid var(--green);color:#b9f5d8}
.msg.err{display:block;background:#3a0f1c;border:1px solid var(--pink);color:#ffc4da}
</style></head><body><div class="wrap">
<div class="brand"><span class="p">Swole</span><span class="g">Mate</span> 💅🏋️</div>
<h1>Hey ${name} 👋</h1><p class="sub">Connect these two things ONCE. After that everything is automatic — no daily chores, ever.</p>
<div class="chips">
<div class="chip ${st.oura ? "on" : ""}">💍 Oura ${st.oura ? "✅ connected" : "· not yet"}</div>
<div class="chip ${st.cron ? "on" : ""}" id="cronChip">🔥 Cronometer ${st.cron ? "✅ connected" : "· not yet"}</div>
</div>

<h2>1 · Your Oura ring 💍</h2>
<div class="card ${st.oura ? "done" : ""}">
${st.oura ? `<p style="margin:0;color:#b9f5d8;font-weight:700">Already connected ✅ Nothing to do here.</p>` : `
<div class="step"><div class="sn">1</div><div>Tap the <b>green button</b> below.</div></div>
<div class="step"><div class="sn">2</div><div>Log in with your <b>Oura email + password</b> (the same one as the Oura app).</div></div>
<div class="step"><div class="sn">3</div><div>Tap <b>"Accept"</b> when Oura asks. That's it — your workouts flow in by themselves. 🎉</div></div>
<a class="btn" href="${ouraUrl}">Connect my Oura</a>`}
<p class="hint">This is how the coach sees your gym sessions + cardio. We never see your Oura password.</p>
</div>

<h2>2 · Your Cronometer 🔥</h2>
<div class="card ${st.cron ? "done" : ""}" id="cronCard">
${st.cron ? `<p style="margin:0;color:#b9f5d8;font-weight:700">Already connected ✅ Nothing to do here.</p>` : `
<div class="step"><div class="sn">1</div><div>Type the <b>same email + password</b> you use to open the Cronometer app.</div></div>
<div class="step"><div class="sn">2</div><div>Tap <b>Connect</b>. We test the login right away, so you'll know instantly if there's a typo.</div></div>
<label>Cronometer email</label><input id="email" type="email" autocomplete="username" placeholder="you@email.com">
<div style="height:12px"></div>
<label>Cronometer password</label><input id="password" type="password" autocomplete="current-password">
<button class="btn" id="save">Connect Cronometer</button>
<div class="msg" id="msg"></div>
<p class="warn">⚠️ If you turned on two-factor login in Cronometer, turn it off first: cronometer.com → Settings → Account.</p>`}
<p class="hint">This is how the coach sees your calories + protein — you just keep logging food like normal.</p>
</div>

<h2>That's the whole setup 🫡</h2>
<div class="card">
<div class="step"><div class="sn">✓</div><div>Both chips green = you're done <b>forever</b>. Keep logging food in Cronometer + wear the ring.</div></div>
<div class="step"><div class="sn">?</div><div>Button not working? Screenshot it and <b>text Medi</b>. 🆘</div></div>
</div>
</div><script>
const $=(i)=>document.getElementById(i);const u=new URLSearchParams(location.search).get("u")||"";
const save=$("save");
if(save)save.addEventListener("click",async()=>{const m=$("msg");m.className="msg";
if(!$("email").value.trim()||!$("password").value){m.className="msg err";m.textContent="Fill in both boxes.";return}
save.disabled=true;save.textContent="Checking your login…";
try{const r=await fetch(location.pathname,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({u,email:$("email").value.trim(),password:$("password").value})});
const d=await r.json();if(!d.ok)throw new Error(d.error||"failed");
m.className="msg ok";m.textContent="Connected ✅ You're done!";save.textContent="Connected ✅";
const c=$("cronChip");c.className="chip on";c.textContent="🔥 Cronometer ✅ connected";$("cronCard").className="card done"}
catch(e){m.className="msg err";m.textContent="Couldn't connect: "+e.message;save.disabled=false;save.textContent="Connect Cronometer"}});
</script></body></html>`;

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  const url = new URL(req.url);
  const sql = postgres(Deno.env.get("SUPABASE_DB_URL"), { prepare: false });
  try {
    if (req.method === "POST") {
      const b = await req.json().catch(() => ({}));
      const token = String(b.u ?? ""), email = String(b.email ?? "").trim(), password = String(b.password ?? "");
      if (!token || !email || !password) return json({ ok: false, error: "missing fields" }, 400);
      const [u] = await sql`select id, display_name from fitness.app_user where health_token = ${token} limit 1`;
      if (!u) return json({ ok: false, error: "unknown link — ask Medi for a fresh one" }, 401);
      if (!(await cronometerLoginWorks(email, password))) return json({ ok: false, error: "Cronometer rejected that email/password (is 2-factor on?)" }, 400);
      await sql`insert into fitness.cronometer_account (user_id, email, password, food_only, updated_at) values (${u.id}, ${email}, ${password}, true, now()) on conflict (user_id) do update set email = excluded.email, password = excluded.password, updated_at = now()`;
      return json({ ok: true, user: u.display_name });
    }
    const token = url.searchParams.get("u") ?? "";
    const [u] = token ? await sql`select id, display_name, health_token from fitness.app_user where health_token = ${token} limit 1` : [];
    if (!u) {
      if (url.searchParams.get("api") === "1") return json({ ok: false, error: "unknown link — ask Medi for a fresh one" }, 401);
      return new Response("Ask Medi for your personal connect link.", { status: 401, headers: { "content-type": "text/plain" } });
    }
    const cfg = await sql`select value from fitness.app_config where key = 'goals_token'`;
    const [oura] = await sql`select 1 from fitness.oura_token where user_id = ${u.id} limit 1`;
    const [cron] = await sql`select 1 from fitness.cronometer_account where user_id = ${u.id} limit 1`;
    const ouraUrl = `${OURA_START}?go=1&token=${encodeURIComponent(cfg[0]?.value ?? "")}&u=${encodeURIComponent(u.health_token)}`;
    if (url.searchParams.get("api") === "1") return json({ ok: true, name: u.display_name, oura: !!oura, cron: !!cron, oura_url: ouraUrl });
    return new Response(page(u.display_name, ouraUrl, { oura: !!oura, cron: !!cron }), { headers: { "content-type": "text/html; charset=utf-8" } });
  } catch (e) {
    return json({ ok: false, error: String(e instanceof Error ? e.message : e) }, 500);
  } finally {
    try { await sql.end(); } catch { /* ignore */ }
  }
});
