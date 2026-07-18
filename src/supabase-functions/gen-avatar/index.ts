// gen-avatar — calls Gemini 2.5 Flash Image (Nano Banana) to turn a photo into a cartoon avatar.
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type",
};
const json = (b, s = 200) => new Response(JSON.stringify(b), { status: s, headers: { ...CORS, "content-type": "application/json" } });

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  const url = new URL(req.url);
  const key = Deno.env.get("GEMINI_API_KEY")?.trim();
  if (url.searchParams.get("ping") === "1") return json({ ok: !!key, keyLen: key ? key.length : 0 });
  if (!key) return json({ ok: false, error: "GEMINI_API_KEY not set" }, 500);
  if (url.searchParams.get("validate") === "1") {
    const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${encodeURIComponent(key)}&pageSize=1`);
    const d = await r.json().catch(() => ({}));
    return json({ ok: r.ok, status: r.status, keyLen: key.length, error: d?.error?.message ?? null, sample: d?.models?.[0]?.name ?? null });
  }
  if (req.method !== "POST") return json({ ok: false, error: "POST only" }, 405);

  try {
    const body = await req.json();
    const prompt = body.prompt ?? "";
    const imageB64 = body.image_base64 ?? "";
    const mime = body.mime ?? "image/jpeg";
    const model = body.model ?? "gemini-2.5-flash-image";
    if (!prompt || !imageB64) return json({ ok: false, error: "need prompt + image_base64" }, 400);

    const parts = [{ text: prompt }, { inline_data: { mime_type: mime, data: imageB64 } }];
    const reqBody = { contents: [{ parts }] };
    if (body.modalities) reqBody.generationConfig = { responseModalities: ["IMAGE"] };

    const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`, {
      method: "POST",
      headers: { "x-goog-api-key": key, "Content-Type": "application/json" },
      body: JSON.stringify(reqBody),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return json({ ok: false, status: res.status, error: data?.error?.message ?? "gemini error", raw: data }, 502);

    const outParts = data?.candidates?.[0]?.content?.parts ?? [];
    let img = null;
    let textOut = "";
    for (const p of outParts) {
      const inl = p.inlineData ?? p.inline_data;
      if (inl?.data) { img = { data: inl.data, mime: inl.mimeType ?? inl.mime_type ?? "image/png" }; break; }
      if (p.text) textOut += p.text;
    }
    if (!img) return json({ ok: false, error: "no image in response", text: textOut, finishReason: data?.candidates?.[0]?.finishReason, raw: data }, 502);
    return json({ ok: true, image_base64: img.data, mime: img.mime });
  } catch (e) {
    return json({ ok: false, error: String(e instanceof Error ? e.message : e) }, 500);
  }
});
