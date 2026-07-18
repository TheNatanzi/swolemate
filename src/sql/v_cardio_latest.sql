-- v_cardio_latest: cardio can arrive from multiple sources per day
-- (phone shortcut = apple_health, oura, cronometer).
-- Take the freshest row PER SOURCE, then keep the single row with the highest
-- minutes. Sources are never summed, so the same run counted by two devices
-- can't double-count. Applied 2026-07-18 (migration v_cardio_latest_max_across_sources).
create or replace view fitness.v_cardio_latest as
with latest_per_source as (
  select distinct on (user_id, log_date, coalesce(raw->>'source', 'cronometer'))
    user_id, log_date, minutes, names, pulled_at
  from fitness.cardio_log
  order by user_id, log_date, coalesce(raw->>'source', 'cronometer'), pulled_at desc
)
select distinct on (user_id, log_date)
  user_id, log_date, minutes, names, pulled_at
from latest_per_source
order by user_id, log_date, minutes desc nulls last, pulled_at desc;
