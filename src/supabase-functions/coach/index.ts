// coach v29 — WEEK SO FAR now matches THE DAILY READ: sorted best-first + stats split onto 2 lines (📝🥩🍽️ | activity·🏋️).
// coach v28 base — SwoleMate engine. meal checks skip users with no data push in 4h (silent pipe ≠ skipped meals). daily-read stats split onto 2 lines (after cal). meal thresholds 20% @4:30p, 70% @9:30p (+ under-pace flavor). daily=1 -> [read, week, gap, LADDER]. meal=am|pm -> meal check. monday=1 -> recap+season+THRONE.
// Ladders: daily streak -> Super Saiyan avatar level; weekly streak -> Game of Thrones level. Start L5 (app_config.ladder_start), ✅=+1 ❌=-1, clamp [1,10].
// Daily ✅ = cals within ±5% + protein ≥95% + steps ≥95% (cardio users: ≥95% of weekly-goal/7). Weekly ✅ = those on week avgs + gym ≥100%.
// Delivery: &tasker=1 -> phone AutoRemote -> WhatsApp GROUP (15s between messages). &send=1 -> Meta DMs. &me=1 = primary only.
import postgres from "https://deno.land/x/postgresjs@v3.4.5/mod.js";
import * as L from "./roast-lines.ts";

const pick = (a) => a[Math.floor(Math.random() * a.length)];
const fill = (s, v) => s.replace(/\{(\w+)\}/g, (_, k) => String(v[k] ?? ""));
const r0 = (n) => Math.round(Number(n) || 0);
const ck = (b) => b ? "✅" : "❌";
const prevDay = (s) => { const d = new Date(s + "T12:00:00Z"); d.setUTCDate(d.getUTCDate() - 1); return d.toISOString().slice(0, 10); };
const laDate = (off = 0) => new Intl.DateTimeFormat("en-CA", { timeZone: "America/Los_Angeles" }).format(new Date(Date.now() + off * 86400000));
const stepsShort = (n) => { const x = r0(n); return x >= 1000 ? String((x / 1000).toFixed(1)).replace(/\.0$/, "") + "k" : String(x); };

const stepPts = (s, g) => g ? r0(Math.min(s / g, 1) * 100) : 0;
const cardioPts = (m, g) => g ? r0(Math.min(m / g, 1) * 100) : 0;
const protPts = (p, g) => g ? r0(Math.min(p / g, 1) * 100) : 0;
function calPts(c, g) { if (!g || !c) return 0; const d = Math.abs(c - g) / g; if (d <= 0.05) return 100; if (d >= 0.2) return 0; return r0((1 - (d - 0.05) / 0.15) * 100); }
const gymTier = (g, goal) => !goal ? "mid" : g >= goal ? "slay" : g > 0 ? "mid" : "flop";
const stepTier = (s, g) => !g ? "mid" : s >= g ? "slay" : s >= g * 0.6 ? "mid" : "flop";
const cardioTier = (m, g) => !g ? "mid" : m >= g ? "slay" : m >= g * 0.6 ? "mid" : "flop";
const protTier = (p, g) => !g ? "close" : p >= g ? "slay" : p >= g * 0.8 ? "close" : "low";
const calTier = (c, g) => !c ? "none" : !g ? "on" : (c / g) > 1.15 ? "over" : (c / g) < 0.8 ? "under" : "on";

function actDaily(s) {
  if (s.metric === "cardio") {
    const hit = !!s.cardioGoal && s.cardioWtd >= s.cardioGoal;
    return { pts: cardioPts(s.cardioWtd, s.cardioGoal), hit, tier: cardioTier(s.cardioWtd, s.cardioGoal), seg: `🏃${r0(s.cardioWtd)}min${ck(hit)}` };
  }
  const hit = !!s.stepsGoal && s.steps >= s.stepsGoal;
  return { pts: stepPts(s.steps, s.stepsGoal), hit, tier: stepTier(s.steps, s.stepsGoal), seg: `👟${stepsShort(s.steps)}${ck(hit)}` };
}
const auraOf = (s) => actDaily(s).pts + protPts(s.prot, s.goalProt) + calPts(s.cal, s.goalCal) + (gymTier(s.gymSessions, s.gymGoal) === "slay" ? 100 : s.gymSessions > 0 ? 50 : 0);
function verdictLine(s) {
  const gt = gymTier(s.gymSessions, s.gymGoal), at = actDaily(s).tier, pt = protTier(s.prot, s.goalProt), ct = calTier(s.cal, s.goalCal);
  const perfect = gt === "slay" && at === "slay" && ct === "on" && pt === "slay";
  const slays = (gt === "slay" ? 1 : 0) + (at === "slay" ? 1 : 0) + (ct === "on" ? 1 : 0) + (pt === "slay" ? 1 : 0);
  return fill(pick(perfect ? L.PERFECT_DAY : slays >= 3 ? L.VERDICT_GREAT : slays >= 1 ? L.VERDICT_MID : L.VERDICT_TRASH), { name: s.name });
}

async function statsForUser(sql, ref = "primary", forDate = null) {
  const [u] = await sql`select u.id, u.display_name, u.whatsapp_to, u.activity_metric from fitness.app_user u where u.cronometer_ref=${ref} limit 1`;
  if (!u) throw new Error(`no user for ref '${ref}'`);
  const days = await sql`select log_date::text, calories, protein_g, food_logged from fitness.v_daily_latest where user_id=${u.id} order by log_date desc limit 40`;
  const act = await sql`select log_date::text, steps from fitness.v_activity_latest where user_id=${u.id} order by log_date desc limit 15`;
  const [gym] = await sql`select coalesce(sum(sessions),0)::int as n from fitness.v_gym_latest where user_id=${u.id} and log_date >= date_trunc('week', current_date)::date`;
  const [card] = await sql`select coalesce(sum(minutes),0)::numeric as m from fitness.v_cardio_latest where user_id=${u.id} and log_date >= date_trunc('week', current_date)::date`;
  const [goal] = await sql`select calorie_goal, protein_goal, gym_goal, steps_goal, cardio_goal from fitness.v_user_goal_latest where user_id=${u.id}`;
  const dayRow = (forDate ? days.find((d) => d.log_date === forDate) : days[0]) || {};
  const actRow = (forDate ? act.find((a) => a.log_date === forDate) : act[0]) || {};
  const logged = new Map(days.map((d) => [d.log_date, !!d.food_logged]));
  let cur = laDate(0); if (logged.get(cur) !== true) cur = prevDay(cur);
  let foodStreak = 0; while (logged.get(cur) === true) { foodStreak++; cur = prevDay(cur); }
  return { ref, name: u.display_name, whatsapp_to: u.whatsapp_to, metric: u.activity_metric || "steps", cal: Number(dayRow.calories ?? 0), prot: Number(dayRow.protein_g ?? 0), steps: Number(actRow.steps ?? 0), cardioWtd: Number(card?.m ?? 0), gymSessions: gym?.n ?? 0, foodStreak, goalCal: goal?.calorie_goal, goalProt: goal?.protein_goal, gymGoal: goal?.gym_goal, stepsGoal: goal?.steps_goal, cardioGoal: goal?.cardio_goal };
}

function userLine(s) {
  const ct = calTier(s.cal, s.goalCal);
  const a = actDaily(s);
  const aura = auraOf(s);
  const logHit = (s.cal > 0 || s.prot > 0), protHit = !!s.goalProt && s.prot >= s.goalProt, calHit = ct === "on", gymHit = !!s.gymGoal && s.gymSessions >= s.gymGoal;
  const line = `*${s.name}* ✨${aura}\n📝${ck(logHit)} 🥩${r0(s.prot)}g${ck(protHit)} 🍽️${r0(s.cal).toLocaleString()}cal${ck(calHit)}\n${a.seg} · 🏋️${s.gymSessions}${ck(gymHit)}\n_${verdictLine(s)}_`;
  return { line, aura };
}
async function podRefs(sql) { return (await sql`select cronometer_ref from fitness.app_user where pod_id = (select pod_id from fitness.app_user where cronometer_ref='primary') and cronometer_ref is not null order by created_at`).map((r) => r.cronometer_ref); }
async function composeGroup(sql) {
  const refs = await podRefs(sql); const arr = [];
  for (const ref of refs) { try { arr.push(await statsForUser(sql, ref, laDate(-1))); } catch { /* skip */ } }
  const blocks = arr.map(userLine).sort((a, b) => b.aura - a.aura).map((x) => x.line);
  return ["☀️ *THE DAILY READ · yesterday*", ...blocks].join("\n\n");
}

async function weekStats(sql, ref, offset = 0) {
  const [u] = await sql`select id, display_name, activity_metric from fitness.app_user where cronometer_ref=${ref} limit 1`;
  if (!u) throw new Error(`no user for ref '${ref}'`);
  const lo = offset === 0 ? sql`date_trunc('week', current_date)::date` : sql`(date_trunc('week', current_date) - interval '7 days')::date`;
  const hi = offset === 0 ? sql`(current_date + 1)` : sql`date_trunc('week', current_date)::date`;
  const [dl] = await sql`select coalesce(round(avg(calories) filter (where food_logged)),0)::int a, coalesce(round(avg(protein_g) filter (where food_logged)),0)::int p, count(*) filter (where food_logged)::int d from fitness.v_daily_latest where user_id=${u.id} and log_date >= ${lo} and log_date < ${hi}`;
  const [ac] = await sql`select coalesce(round(avg(steps)),0)::int s from fitness.v_activity_latest where user_id=${u.id} and log_date >= ${lo} and log_date < ${hi} and steps is not null`;
  const [cd] = await sql`select coalesce(sum(minutes),0)::numeric m from fitness.v_cardio_latest where user_id=${u.id} and log_date >= ${lo} and log_date < ${hi}`;
  const [gm] = await sql`select coalesce(sum(sessions),0)::int g from fitness.v_gym_latest where user_id=${u.id} and log_date >= ${lo} and log_date < ${hi}`;
  const [g] = await sql`select calorie_goal, protein_goal, gym_goal, steps_goal, cardio_goal from fitness.v_user_goal_latest where user_id=${u.id}`;
  return { id: u.id, name: u.display_name, metric: u.activity_metric || "steps", avgCal: dl?.a ?? 0, avgProt: dl?.p ?? 0, loggedDays: dl?.d ?? 0, avgSteps: ac?.s ?? 0, cardioTotal: Number(cd?.m ?? 0), gym: gm?.g ?? 0, goalCal: g?.calorie_goal, goalProt: g?.protein_goal, gymGoal: g?.gym_goal, stepsGoal: g?.steps_goal, cardioGoal: g?.cardio_goal };
}
function actWeek(w) {
  if (w.metric === "cardio") {
    const hit = !!w.cardioGoal && w.cardioTotal >= w.cardioGoal;
    return { pt: hit ? 1 : 0, seg: `🏃${r0(w.cardioTotal)}min${ck(hit)}` };
  }
  const hit = !!w.stepsGoal && w.avgSteps >= w.stepsGoal;
  return { pt: hit ? 1 : 0, seg: `👟${stepsShort(w.avgSteps)}${ck(hit)}` };
}
function league5(w, needDays) {
  const logPt = w.loggedDays >= needDays ? 1 : 0;
  const protPt = w.goalProt && w.avgProt >= w.goalProt ? 1 : 0;
  const calPt = w.goalCal && Math.abs(w.avgCal - w.goalCal) / w.goalCal <= 0.15 ? 1 : 0;
  const actPt = actWeek(w).pt;
  const gymPt = w.gymGoal && w.gym >= w.gymGoal ? 1 : 0;
  return { score: logPt + protPt + calPt + actPt + gymPt, logPt, protPt, calPt, actPt, gymPt };
}
async function weekAll(sql, offset = 0) {
  const daysElapsed = offset === 0 ? (new Date().getUTCDay() + 6) % 7 + 1 : 7;
  const refs = await podRefs(sql); const out = [];
  for (const ref of refs) { try { const w = await weekStats(sql, ref, offset); out.push({ ...w, ...league5(w, daysElapsed), daysElapsed }); } catch { /* skip */ } }
  return out;
}
function composeWTD(arr) {
  const blocks = [...arr].sort((a, b) => b.score - a.score).map((w) => `*${w.name}*  (${w.score}/5)\n📝${w.loggedDays}/${w.daysElapsed}${ck(w.logPt)} 🥩${w.avgProt}g${ck(w.protPt)} 🍽️${w.avgCal.toLocaleString()}cal${ck(w.calPt)}\n${actWeek(w).seg} · 🏋️${w.gym}${ck(w.gymPt)}`);
  return ["📊 *WEEK SO FAR* · avg/day", ...blocks].join("\n\n");
}

function composeCloseGap(rows) {
  const blocks = rows.map((w) => {
    const elapsed = w.daysElapsed || 1;
    const done = Math.max(elapsed - 1, 0);
    const left = Math.max(8 - elapsed, 1);
    const n = [];
    if (w.metric === "cardio") {
      if (w.cardioGoal) { const rem = w.cardioGoal - w.cardioTotal; if (rem > 0) n.push(`🏃 ${r0(rem)} more cardio min this week (~${r0(rem / left)}/day)`); }
    } else if (w.stepsGoal) {
      const need = (w.stepsGoal * 7 - w.avgSteps * done) / left;
      if (need > w.stepsGoal + 50) n.push(`👟 walk ${stepsShort(need)}/day the rest of the week`);
    }
    if (w.goalProt) { const need = (w.goalProt * 7 - w.avgProt * done) / left; if (need > w.goalProt + 1) n.push(`🥩 ${r0(need)}g protein/day to catch up`); }
    if (w.goalCal && done > 0) {
      const need = (w.goalCal * 7 - w.avgCal * done) / left;
      const dev = (w.avgCal - w.goalCal) / w.goalCal;
      const cd = r0(need).toLocaleString();
      if (dev > 0.20) n.push(need < 0 ? `🍽️ blew the weekly budget — damage control the rest of the week 😬` : `🍽️ big surplus — reel it in to ${cd}cal/day to get back on budget`);
      else if (dev > 0.05) n.push(`🍽️ ease up — average ${cd}cal/day to land on budget`);
      else if (dev < -0.20) n.push(`🍽️ don't starve yourself 🍗 you can eat up to ${cd}cal/day — muscles need fuel`);
      else if (dev < -0.05) n.push(`🍽️ nice restraint 👏 room for up to ${cd}cal/day and still on budget`);
    }
    if (w.gymGoal && w.gym === 0 && elapsed >= 4) n.push(`🏋️ no workouts logged yet — forget to enter it, or better get busy to hit your ${w.gymGoal} this week 😤`);
    const hasGoals = !!(w.goalProt || w.goalCal || w.stepsGoal || w.cardioGoal);
    const body = n.length ? n.map((x) => `  ${x}`).join("\n") : (hasGoals ? "  🎯 on pace — keep it up" : "  set your goals to get nudges");
    return `*${w.name}*\n${body}`;
  });
  return ["🎯 *CLOSE THE GAP* · lock in for the rest of the week", ...blocks].join("\n\n");
}

// Meal-logging checks (TODAY's running calorie total as a proxy for "have you logged?")
const MEAL_AM = [
  `diary's still empty and it's the afternoon — log your breakfast + lunch 👀`,
  `breakfast? lunch? hello?? your food log is a ghost town 👻`,
  `it's the afternoon and you've logged NOTHING. the fork won't lift itself 🍴`,
  `half the day gone and the diary's blanker than your excuses 📓`,
  `we KNOW you ate. the log says otherwise. one of you is lying 🤨`,
  `your macros called — they're filing a missing person report 🚨`,
  `no breakfast, no lunch?? either you're a monk or you're slacking. log it`,
  `the diary is giving abandoned warehouse. haunted. LOG.`,
  `photosynthesis isn't real for humans bestie — log what you actually ate ☀️`,
  `two meals unaccounted for. this isn't a mystery novel, it's a food log 🔎`,
  `mother checked the diary and GASPED. nothing?? at THIS hour??`,
  `if it isn't logged it didn't happen — and neither did your progress 💅`,
  `the group can see your empty diary. we're not judging. we're ABSOLUTELY judging 👀`,
  `it's giving intermittent fasting by ACCIDENT. log your meals bestie`,
  `your food log said "no thoughts, head empty" today. fix that 📓`,
  `breakfast AND lunch missing?? call the detectives, two meals just vanished 🕵️`,
  `the fridge saw you. the log didn't. make them agree ✍️`,
  `an empty diary at 4pm is a personality flaw. redeemable, but barely`,
  `mother didn't build this app for you to gaslight the food log 🙄`,
  `logging takes less time than reading this roast. PROVE IT`,
  `you're not mysterious for not logging, you're just behind 💅`,
  `the diary is on a hunger strike apparently. negotiate. log something`,
  `zero entries?? even Jabba the Hutt logs his burgers 🍔`,
  `we track five pillars and you're currently offering NONE. rally.`,
  `your protein doesn't count if it's a secret. declassify the meals 📂`,
];
const MEAL_PM = [
  `day's looking light — did dinner get logged, or ghosted? 🍽️`,
  `calories suspiciously low for this hour. log that dinner 👀`,
  `either you're fasting or you forgot to log dinner. we're betting forgot 💀`,
  `it's almost bedtime and the diary's still hungry. feed it your dinner 📓`,
  `your log ends at lunch like a cliffhanger. we need the season finale 🍿`,
  `dinner happened. we ALL know dinner happened. WRITE IT DOWN ✍️`,
  `the numbers say you're starving. the vibes say you forgot to log 🤔`,
  `logging dinner takes 45 seconds. getting roasted in here lasts forever 💅`,
  `mother refuses to believe you ate air tonight. log the dinner, bestie`,
  `last call 🔔 the day closes soon and your diary's half-finished`,
  `that calorie count is giving "oops i forgot". fix it before midnight 🕛`,
  `skipping the log ≠ skipping the calories. they still count. LOG.`,
  `the kitchen closed but the log's still open. finish the job ✍️`,
  `you gonna let a 45-second task beat you? log the dinner, champion 💪`,
  `unlogged dinner detected. this is a certified flop-era warning 🚨`,
  `the day's almost over and your diary reads like a skipped chapter 📖`,
  `mother sees a half-empty log and raises ONE eyebrow. just one. 🤨`,
  `your dinner is currently off the record. this isn't a deposition. LOG IT`,
  `imagine grinding all day and losing it to a missing dinner entry 💀`,
  `the scale knows. the log should too. write the dinner down`,
  `dinner unlogged = tomorrow's roast pre-ordered. cancel the order ✍️`,
  `we're one dinner entry away from peace tonight. give it to us 🕊️`,
  `your macros are sitting in the dark waiting to be counted. free them`,
  `night night... unless that dinner's still unlogged?? then WAKE UP ✍️`,
  `the diary closes at midnight like cinderella. log it before it turns into a pumpkin 🎃`,
];
const MEAL_PM_UNDER = [
  `logged but {n} cal under pace — dessert is ON THE TABLE tonight 🍨`,
  `you're {n} cal behind pace. a snack stands between you and glory 🥜`,
  `so close — {n} more cal to hit tonight's pace. finish strong 💪`,
  `the log's alive but light: {n} cal under. mother prescribes a protein shake 🥤`,
  `{n} cal short and the kitchen's still open. this is fixable, bestie`,
  `under pace by {n} cal. eat something or accept tomorrow's roast 💅`,
  `your macros are {n} cal behind schedule. late-night fuel run? 🌙`,
  `almost there — {n} cal under pace. don't leave gains on the counter`,
];
async function composeMealCheck(sql, phase) {
  const today = laDate(0);
  const refs = await podRefs(sql);
  const thresh = phase === "am" ? 0.20 : 0.70; // 20% by 3:30 data / 70% by 9pm data (shortcut pushes 6a,3:30p,9p,11:30p)
  const miss = [];
  for (const ref of refs) {
    const [u] = await sql`select id, display_name from fitness.app_user where cronometer_ref=${ref} limit 1`;
    if (!u) continue;
    const [g] = await sql`select calorie_goal from fitness.v_user_goal_latest where user_id=${u.id}`;
    if (!g?.calorie_goal) continue;
    // Data-freshness gate: if their pipe hasn't delivered ANYTHING in 4h, assume the phone is silent (not that they skipped meals) — leave them out of the nudge.
    const [f] = await sql`select greatest(
      (select max(pulled_at) from fitness.daily_log where user_id=${u.id}),
      (select max(pulled_at) from fitness.activity_log where user_id=${u.id}),
      (select max(pulled_at) from fitness.cardio_log where user_id=${u.id})
    ) as last_push`;
    if (!f?.last_push || (Date.now() - new Date(f.last_push).getTime()) > 4 * 3600 * 1000) continue;
    const [d] = await sql`select coalesce(calories,0)::numeric cal from fitness.v_daily_latest where user_id=${u.id} and log_date=${today}`;
    const cal = Number(d?.cal ?? 0);
    if (cal < g.calorie_goal * thresh) miss.push({ name: u.display_name, cal, gap: Math.round(g.calorie_goal * thresh - cal) });
  }
  if (!miss.length) return null;
  const header = phase === "am" ? "🍳 *DID YOU EAT?* · breakfast + lunch check" : "🍽️ *DINNER CHECK*";
  const used = new Set();
  const line = (pool) => { let l = pick(pool); let guard = 0; while (used.has(l) && guard++ < 20) l = pick(pool); used.add(l); return l; };
  return [header, ...miss.map((p) => {
    const pool = (phase === "pm" && p.cal > 0) ? MEAL_PM_UNDER : (phase === "am" ? MEAL_AM : MEAL_PM);
    return `*${p.name}* — ${fill(line(pool), { n: p.gap })}`;
  })].join("\n\n");
}

const MEDALS = ["gold", "silver", "bronze", "poop"];
const MEDAL_EMOJI = { gold: "🥇", silver: "🥈", bronze: "🥉", poop: "💩" };
const MEDAL_PTS = { gold: 3, silver: 2, bronze: 1, poop: 0 };
function rankMedals(rows) {
  rows.sort((a, b) => b.score - a.score);
  let prev = null, rank = 0;
  rows.forEach((r, i) => { if (r.score !== prev) { rank = i; prev = r.score; } r.medal = r.score === 0 ? "poop" : MEDALS[Math.min(rank, 3)]; r.points = MEDAL_PTS[r.medal]; });
  return rows;
}
async function finalizeWeek(sql) {
  const [meta] = await sql`select gc.pod_id, gc.season_weeks, (date_trunc('week', current_date) - interval '7 days')::date as week_start, (floor((((date_trunc('week', current_date) - interval '7 days')::date) - gc.season_start)/7) + 1)::int as season_week from fitness.game_config gc where gc.pod_id = (select pod_id from fitness.app_user where cronometer_ref='primary')`;
  const rows = rankMedals(await weekAll(sql, -1));
  for (const r of rows) {
    await sql`insert into fitness.league_week (pod_id, user_id, season_week, week_start, score, medal, points) values (${meta.pod_id}, ${r.id}, ${meta.season_week}, ${meta.week_start}, ${r.score}, ${r.medal}, ${r.points}) on conflict (user_id, week_start) do nothing`;
  }
  return { rows, meta };
}
async function composeLastWeek(sql) {
  const { rows } = await finalizeWeek(sql);
  const blocks = rows.map((r, i) => {
    const tag = i === 0 && r.score > 0 ? " — 👑 Bragging Rights of the Week" : (r.score === 0 ? " — crickets 🦗" : "");
    const detail = `🥩${r.avgProt}g${ck(r.protPt)} 🍽️${r.avgCal.toLocaleString()}cal${ck(r.calPt)} ${actWeek(r).seg} · 🏋️${r.gym}${ck(r.gymPt)} · 📝${r.loggedDays}/7${ck(r.logPt)}`;
    return `${MEDAL_EMOJI[r.medal]} *${r.name}* ${r.score}/5${tag}\n${detail}`;
  });
  return ["🏁 *LAST WEEK'S RESULTS* · avg/day", ...blocks].join("\n\n");
}
async function seasonMeta(sql) {
  const [m] = await sql`select gc.pod_id, gc.season_weeks, gc.season_start, (floor((current_date - gc.season_start)/7) + 1)::int as week_num, (floor(((date_trunc('week', current_date) - interval '7 days')::date - gc.season_start)/7) + 1)::int as prev_week_num from fitness.game_config gc where gc.pod_id = (select pod_id from fitness.app_user where cronometer_ref='primary')`;
  return m;
}
async function seasonTable(sql, meta) {
  return await sql`select au.display_name name, coalesce(sum(lw.points),0)::int pts, array_remove(array_agg(lw.medal order by lw.week_start), null) medals from fitness.app_user au left join fitness.league_week lw on lw.user_id=au.id and lw.week_start >= ${meta.season_start} where au.pod_id=${meta.pod_id} and au.cronometer_ref is not null group by au.display_name order by pts desc`;
}
async function composeSeason(sql) {
  const meta = await seasonMeta(sql);
  const rows = await seasonTable(sql, meta);
  const lines = rows.map((r, i) => `${i + 1}. *${r.name}* — ${r.pts} pts ${(r.medals || []).map((m) => MEDAL_EMOJI[m]).join("")}`);
  const head = `🏆 *THE CHALLENGE · Week ${meta.week_num} of ${meta.season_weeks}*`;
  const finalWeek = meta.week_num >= meta.season_weeks ? "\n⚔️ *FINAL WEEK — everything on the line*" : "";
  return [head + finalWeek, ...lines].join("\n");
}
// Season finale: crown the champion, then auto-restart. Next length = app_config.next_season_weeks (4/6/8/12), default 4.
async function composeFinale(sql, meta) {
  const rows = await seasonTable(sql, meta);
  const champ = rows[0]; const last = rows[rows.length - 1];
  const lines = rows.map((r, i) => `${i + 1}. *${r.name}* — ${r.pts} pts ${(r.medals || []).map((m) => MEDAL_EMOJI[m]).join("")}`);
  const [nx] = await sql`select value from fitness.app_config where key='next_season_weeks' limit 1`;
  const next = [4, 6, 8, 12].includes(parseInt(nx?.value)) ? parseInt(nx.value) : 4;
  return [
    `👑🏆 *SEASON OVER — YOUR CHAMPION: ${champ?.name ?? "nobody"}* 🏆👑`,
    `${meta.season_weeks} weeks of war. ${champ?.name ?? "nobody"} takes eternal bragging rights. ${last && last !== champ ? `${last.name} takes the L — build a shrine to it 💀` : ""}`,
    `*FINAL TABLE*\n${lines.join("\n")}`,
    `_⚔️ NEW BATTLE STARTS TODAY: ${next} weeks. Leader can change it (4/6/8/12) before next Monday — otherwise ${next} it is._`,
  ].join("\n\n");
}
async function resetSeason(sql) {
  const [nx] = await sql`select value from fitness.app_config where key='next_season_weeks' limit 1`;
  const next = [4, 6, 8, 12].includes(parseInt(nx?.value)) ? parseInt(nx.value) : 4;
  await sql`update fitness.game_config set season_start = date_trunc('week', current_date)::date, season_weeks = ${next}, updated_at = now() where pod_id = (select pod_id from fitness.app_user where cronometer_ref='primary')`;
  await sql`delete from fitness.app_config where key='next_season_weeks'`;
  return next;
}

// ===== STREAK LADDERS -> AVATAR LEVELS =====
// Daily ladder = Super Saiyan set (moves every day). Weekly ladder = Game of Thrones set (moves every completed Mon-Sun week).
const SS_TIERS = ["Jabba the Hutt", "Soda Slob", "Fry Fiend", "Donut Sulker", "Fresh Start", "Warming Up", "Pumped", "Iron Presser", "Deadlift Beast", "SUPER SAIYAN"];
const GOT_M = ["Flea Bottom Peasant", "Gutter Urchin", "Tavern Servant", "Conscript Spearman", "Sellsword", "Anointed Knight", "Landed Lord", "Warden of the Realm", "Crowned King", "TARGARYEN DRAGONLORD"];
const GOT_F = ["Flea Bottom Peasant", "Gutter Urchin", "Tavern Servant", "Conscript Spearwoman", "Sellsword", "Anointed Knight", "Landed Lady", "Warden of the Realm", "Crowned Queen", "TARGARYEN DRAGON QUEEN"];
const addDays = (s, n) => { const d = new Date(s + "T12:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
const mondayOnOrAfter = (s) => { const d = new Date(s + "T12:00:00Z"); const off = (8 - d.getUTCDay()) % 7; return addDays(s, off); };
const within5 = (v, goal) => !!goal && goal > 0 && Math.abs(v - goal) / goal <= 0.05;
const atLeast95 = (v, goal) => !!goal && goal > 0 && v >= goal * 0.95;

async function ladderData(sql) {
  const [ls] = await sql`select value from fitness.app_config where key='ladder_start' limit 1`;
  const start = ls?.value || laDate(0);
  const users = await sql`select id, display_name, gender, activity_metric from fitness.app_user where pod_id=(select pod_id from fitness.app_user where cronometer_ref='primary') and cronometer_ref is not null order by created_at`;
  const out = [];
  for (const u of users) {
    const [g] = await sql`select calorie_goal, protein_goal, gym_goal, steps_goal, cardio_goal from fitness.v_user_goal_latest where user_id=${u.id}`;
    if (!g || !(g.calorie_goal || g.protein_goal)) continue; // not onboarded yet -> no ladder line
    const days = await sql`select log_date::text d, calories c, protein_g p from fitness.v_daily_latest where user_id=${u.id} and log_date >= ${start}`;
    const acts = await sql`select log_date::text d, steps s from fitness.v_activity_latest where user_id=${u.id} and log_date >= ${start}`;
    const cards = await sql`select log_date::text d, minutes m from fitness.v_cardio_latest where user_id=${u.id} and log_date >= ${start}`;
    const gyms = await sql`select log_date::text d, sessions n from fitness.v_gym_latest where user_id=${u.id} and log_date >= ${start}`;
    out.push({ ...u, metric: u.activity_metric || "steps", goals: g, start,
      days: new Map(days.map((r) => [r.d, r])), acts: new Map(acts.map((r) => [r.d, Number(r.s)])),
      cards: new Map(cards.map((r) => [r.d, Number(r.m)])), gyms: new Map(gyms.map((r) => [r.d, Number(r.n)])) });
  }
  return out;
}
function dayPass(u, date) {
  const d = u.days.get(date);
  const calOk = within5(Number(d?.c ?? 0), u.goals.calorie_goal);
  const protOk = atLeast95(Number(d?.p ?? 0), u.goals.protein_goal);
  const actOk = u.metric === "cardio" ? atLeast95(u.cards.get(date) ?? 0, (u.goals.cardio_goal || 0) / 7) : atLeast95(u.acts.get(date) ?? 0, u.goals.steps_goal);
  return calOk && protOk && actOk;
}
function dailyLadder(u) {
  let lvl = 5, last = null;
  const yest = laDate(-1);
  for (let date = u.start; date <= yest; date = addDays(date, 1)) {
    last = dayPass(u, date);
    lvl = Math.max(1, Math.min(10, lvl + (last ? 1 : -1)));
  }
  return { lvl, moved: last };
}
function weekPass(u, ws) {
  let calSum = 0, calN = 0, protSum = 0, stepSum = 0, stepN = 0, cardio = 0, gym = 0;
  for (let date = ws; date <= addDays(ws, 6); date = addDays(date, 1)) {
    const d = u.days.get(date);
    if (d && Number(d.c) > 0) { calSum += Number(d.c); calN++; protSum += Number(d.p); }
    const s = u.acts.get(date); if (s != null) { stepSum += s; stepN++; }
    cardio += u.cards.get(date) ?? 0; gym += u.gyms.get(date) ?? 0;
  }
  const calOk = within5(calN ? calSum / calN : 0, u.goals.calorie_goal);
  const protOk = atLeast95(calN ? protSum / calN : 0, u.goals.protein_goal);
  const actOk = u.metric === "cardio" ? atLeast95(cardio, u.goals.cardio_goal) : atLeast95(stepN ? stepSum / stepN : 0, u.goals.steps_goal);
  const gymOk = !!u.goals.gym_goal && gym >= u.goals.gym_goal; // gym must be 100%+
  return calOk && protOk && actOk && gymOk;
}
function weeklyLadder(u) {
  let lvl = 5, last = null;
  const today = laDate(0);
  for (let ws = mondayOnOrAfter(u.start); addDays(ws, 7) <= today; ws = addDays(ws, 7)) {
    last = weekPass(u, ws);
    lvl = Math.max(1, Math.min(10, lvl + (last ? 1 : -1)));
  }
  return { lvl, moved: last };
}
const UP_LINES = [`climbed. the glow-up is REAL`, `ascending!! gagged`, `up a level. mother is EVOLVING`, `leveled UP. the ladder trembles`];
const DOWN_LINES = [`slipped a level. gravity said hi 💀`, `DOWN a level. the decay is showing`, `dropped. your avatar felt that`, `sank a rung. embarrassing for you`];
function ladderLine(name, lvl, title, moved, unit = "day") {
  const arrow = moved == null ? "▪️" : moved ? "🔺" : "🔻";
  const note = moved == null ? `fresh start — ${unit} 1` : pick(moved ? UP_LINES : DOWN_LINES);
  return `${arrow} *${name}* — *L${lvl}: ${title}*\n_${note}_`;
}
async function composeLadderDaily(sql) {
  const us = await ladderData(sql);
  if (!us.length) return null;
  const rows = us.map((u) => { const r = dailyLadder(u); return { name: u.display_name, ...r }; }).sort((a, b) => b.lvl - a.lvl);
  const lines = rows.map((r) => ladderLine(r.name, r.lvl, SS_TIERS[r.lvl - 1], r.moved));
  return ["⚡ *THE LADDER · daily avatar*", ...lines, "_hit your day (cals · protein · steps, all within 5%) = climb. miss = sink. L1 Jabba the Hutt ⇄ L10 SUPER SAIYAN_"].join("\n\n");
}
async function composeLadderWeekly(sql) {
  const us = await ladderData(sql);
  if (!us.length) return null;
  const rows = us.map((u) => { const r = weeklyLadder(u); const t = ((u.gender || "M").toUpperCase().startsWith("F") ? GOT_F : GOT_M)[r.lvl - 1]; return { name: u.display_name, lvl: r.lvl, title: t, moved: r.moved }; }).sort((a, b) => b.lvl - a.lvl);
  const lines = rows.map((r) => ladderLine(r.name, r.lvl, r.title, r.moved, "week"));
  return ["🐉 *THE THRONE ROOM · weekly avatar*", ...lines, "_win the week (cals · protein · steps within 5% + gym 100%) to rise from Flea Bottom to the Iron Throne_"].join("\n\n");
}

async function waSend(payload) {
  const phoneId = Deno.env.get("WHATSAPP_PHONE_NUMBER_ID"); const token = Deno.env.get("WHATSAPP_ACCESS_TOKEN");
  const res = await fetch(`https://graph.facebook.com/v23.0/${phoneId}/messages`, { method: "POST", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }, body: JSON.stringify({ messaging_product: "whatsapp", ...payload }) });
  return { sent: res.ok, status: res.status, body: await res.json().catch(() => ({})) };
}
const sendText = (to, text) => waSend({ to, type: "text", text: { body: text } });

Deno.serve(async (req) => {
  const q = new URL(req.url).searchParams;
  const sql = postgres(Deno.env.get("SUPABASE_DB_URL"), { prepare: false });
  try {
    async function primaryTo() { const [pu] = await sql`select whatsapp_to from fitness.app_user where cronometer_ref='primary' limit 1`; return pu?.whatsapp_to; }
    async function recipients() { return (await sql`select whatsapp_to from fitness.app_user where pod_id = (select pod_id from fitness.app_user where cronometer_ref='primary') and whatsapp_to is not null order by created_at`).map((r) => r.whatsapp_to); }
    async function out(msgs) {
      const arr = (Array.isArray(msgs) ? msgs : [msgs]).filter(Boolean);
      if (q.get("tasker") === "1") {
        const [cfg] = await sql`select value from fitness.app_config where key='autoremote_key' limit 1`;
        if (!cfg?.value) return { ok: false, error: "no autoremote_key in app_config", messages: arr };
        const sent = [];
        for (let i = 0; i < arr.length; i++) {
          const u = "https://autoremotejoaomgcd.appspot.com/sendmessage?key=" + cfg.value + "&message=" + encodeURIComponent("swole=:=" + arr[i]);
          let ok = false, status = 0;
          try { const r = await fetch(u); ok = r.ok; status = r.status; } catch { status = -1; }
          sent.push({ via: "tasker", ok, status });
          if (i < arr.length - 1) await new Promise((res) => setTimeout(res, 15000));
        }
        return { ok: sent.every((s) => s.ok), sent, messages: arr };
      }
      if (q.get("send") === "1") {
        const tos = q.get("me") === "1" ? [await primaryTo()].filter(Boolean) : await recipients();
        if (!tos.length) return { ok: false, error: "no recipients", messages: arr };
        const sent = [];
        for (const to of tos) for (const m of arr) { const r = await sendText(to, m); sent.push({ to, sent: r.sent, status: r.status, error: r.body?.error?.message }); }
        return { ok: sent.every((s) => s.sent), sent, messages: arr };
      }
      return { ok: true, messages: arr };
    }
    if (q.get("meal")) { const msg = await composeMealCheck(sql, q.get("meal") === "pm" ? "pm" : "am"); if (!msg) return Response.json({ ok: true, skipped: "everyone logged" }); return Response.json(await out(msg)); }
    if (q.get("daily") === "1") { const wk = await weekAll(sql, 0); return Response.json(await out([await composeGroup(sql), composeWTD(wk), composeCloseGap(wk), await composeLadderDaily(sql)])); }
    if (q.get("group") === "1") return Response.json(await out(await composeGroup(sql)));
    if (q.get("wtd") === "1") return Response.json(await out(composeWTD(await weekAll(sql, 0))));
    if (q.get("gap") === "1") return Response.json(await out(composeCloseGap(await weekAll(sql, 0))));
    if (q.get("ladder") === "1") return Response.json(await out(await composeLadderDaily(sql)));
    if (q.get("throne") === "1") return Response.json(await out(await composeLadderWeekly(sql)));
    if (q.get("monday") === "1") {
      const meta = await seasonMeta(sql);
      const msgs = [await composeLastWeek(sql)];
      if (meta && meta.prev_week_num >= meta.season_weeks) {
        msgs.push(await composeFinale(sql, meta));
        if (q.get("dry") !== "1") await resetSeason(sql);
        msgs.push(await composeSeason(sql)); // fresh season standings
      } else {
        msgs.push(await composeSeason(sql));
      }
      msgs.push(await composeLadderWeekly(sql));
      return Response.json(await out(msgs));
    }
    return Response.json({ ok: true, modes: ["daily", "meal=am|pm", "group", "wtd", "gap", "ladder", "throne", "monday"], hint: "&tasker=1 -> group via phone" });
  } catch (e) {
    return Response.json({ ok: false, error: String(e instanceof Error ? e.message : e) }, { status: 500 });
  } finally { try { await sql.end(); } catch { /* ignore */ } }
});
