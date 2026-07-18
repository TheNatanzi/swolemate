// oura-oauth v8 — connects a squad member's Oura account.
// Start: ?go=1&token=<goals_token>&u=<health_token>  (u omitted -> primary user, back-compat).
// The health_token rides through OAuth `state` as "<goals_token>.<health_token>" so the callback
// knows which app_user to store the tokens for.
import postgres from "https://deno.land/x/postgresjs@v3.4.5/mod.js";

const CALLBACK = "https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/oura-oauth";
const AUTHORIZE = "https://cloud.ouraring.com/oauth/authorize";
const TOKEN = "https://api.ouraring.com/oauth/token";
const SCOPE = "daily workout personal";

const html = (msg, status = 200) => new Response(
  `<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><body style="font-family:-apple-system,sans-serif;background:#0b141a;color:#e9edef;display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0"><div style="max-width:420px;padding:24px;text-align:center"><h1 style="color:#00a884">${msg}</h1></div></body>`,
  { status, headers: { "content-type": "text/html; charset=utf-8" } });

Deno.serve(async (req) => {
  const url = new URL(req.url);
  const clientId = (Deno.env.get("OURA_CLIENT_ID") ?? "").trim();
  const clientSecret = (Deno.env.get("OURA_CLIENT_SECRET") ?? "").trim();
  const sql = postgres(Deno.env.get("SUPABASE_DB_URL"), { prepare: false });
  try {
    if (url.searchParams.get("debug") === "1") {
      return Response.json({ clientIdLen: clientId.length, clientIdTail: clientId.slice(-6), secretLen: clientSecret.length, secretTail: clientSecret.slice(-4), rawSecretLen: (Deno.env.get("OURA_CLIENT_SECRET") ?? "").length });
    }
    const cfg = await sql`select value from fitness.app_config where key = 'goals_token'`;
    const goodToken = cfg[0]?.value;

    if (url.searchParams.get("go") === "1") {
      if (!clientId) return html("Oura not configured yet (missing OURA_CLIENT_ID)", 500);
      if (url.searchParams.get("token") !== goodToken) return html("Not authorized", 401);
      const healthToken = (url.searchParams.get("u") ?? "").replace(/[^a-f0-9]/gi, "");
      const auth = new URL(AUTHORIZE);
      auth.searchParams.set("response_type", "code");
      auth.searchParams.set("client_id", clientId);
      auth.searchParams.set("redirect_uri", CALLBACK);
      auth.searchParams.set("scope", SCOPE);
      auth.searchParams.set("state", healthToken ? `${goodToken}.${healthToken}` : goodToken);
      return Response.redirect(auth.toString(), 302);
    }

    const code = url.searchParams.get("code");
    const state = url.searchParams.get("state") ?? "";
    if (code) {
      const [stateToken, healthToken] = state.split(".");
      if (stateToken !== goodToken) return html("Security check failed (state mismatch)", 400);
      if (!clientId || !clientSecret) return html("Oura not configured (missing client id/secret)", 500);
      const res = await fetch(TOKEN, {
        method: "POST",
        headers: { "content-type": "application/x-www-form-urlencoded", "Authorization": "Basic " + btoa(`${clientId}:${clientSecret}`) },
        body: new URLSearchParams({ grant_type: "authorization_code", code, redirect_uri: CALLBACK }).toString(),
      });
      const tok = await res.json().catch(() => ({}));
      if (!tok.access_token) return html("Connection failed: " + JSON.stringify(tok).slice(0, 160), 500);
      const [u] = healthToken
        ? await sql`select id, display_name from fitness.app_user where health_token = ${healthToken} limit 1`
        : await sql`select id, display_name from fitness.app_user where cronometer_ref = 'primary' limit 1`;
      if (!u) return html("Unknown user for this connect link", 400);
      const expires = new Date(Date.now() + (tok.expires_in ?? 86400) * 1000).toISOString();
      await sql`insert into fitness.oura_token (user_id, access_token, refresh_token, expires_at, updated_at) values (${u.id}, ${tok.access_token}, ${tok.refresh_token}, ${expires}, now()) on conflict (user_id) do update set access_token = excluded.access_token, refresh_token = excluded.refresh_token, expires_at = excluded.expires_at, updated_at = now()`;
      return html(`Oura connected for ${u.display_name}! ✅ You can close this tab.`);
    }
    return html("Fitness Oura connector");
  } catch (e) {
    return html("Error: " + String(e instanceof Error ? e.message : e), 500);
  } finally {
    try { await sql.end(); } catch { /* ignore */ }
  }
});
