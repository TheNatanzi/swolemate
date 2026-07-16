-- ROLLBACK: re-enable the Tasker/AutoRemote delivery route (pg_cron -> coach?...&tasker=1 -> phone Tasker).
-- Use if the PC-sender path fails. Times are UTC (17:00 = 10am PDT; in PST winter use 18:00/00:30/05:30/20:00).
-- Also disable the Windows tasks: PowerShell> Get-ScheduledTask | ? TaskName -like "SwoleMate*" | Disable-ScheduledTask
-- <ANON> = the anon key from Supabase get_publishable_keys.

SELECT cron.schedule('swolemate-daily-read', '0 17 * * *', $$
  SELECT net.http_post(
    url := 'https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/coach?daily=1&tasker=1',
    headers := jsonb_build_object('Content-Type','application/json','Authorization','Bearer <ANON>'));
$$);
SELECT cron.schedule('swolemate-meal-am', '30 23 * * *', $$
  SELECT net.http_post(url := 'https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/coach?meal=am&tasker=1',
    headers := jsonb_build_object('Content-Type','application/json','Authorization','Bearer <ANON>'));
$$);
SELECT cron.schedule('swolemate-meal-pm', '30 4 * * *', $$
  SELECT net.http_post(url := 'https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/coach?meal=pm&tasker=1',
    headers := jsonb_build_object('Content-Type','application/json','Authorization','Bearer <ANON>'));
$$);
SELECT cron.schedule('swolemate-monday-recap', '0 19 * * 1', $$
  SELECT net.http_post(
    url := 'https://lxuvaggznyvgqxknlnvp.supabase.co/functions/v1/coach?monday=1&tasker=1',
    headers := jsonb_build_object('Content-Type','application/json','Authorization','Bearer <ANON>'));
$$);
-- The Tasker profiles remain installed on the Pixel; they reactivate automatically when AutoRemote messages arrive.
