-- supabase-only: needs pg_cron (enabled in the Supabase dashboard). Skipped by the local PGlite tests.

create extension if not exists pg_cron;

-- Remove expired LLM / vision cache entries every hour.
select cron.schedule('happygut-expire-llm-cache', '7 * * * *',
  $$delete from cache.llm_cache where expires_at < now()$$);

-- Create next months' event partitions on the 1st of each month.
select cron.schedule('happygut-ensure-partitions', '13 0 1 * *',
  $$select events.ensure_partitions(3)$$);

-- Meal-photo retention (30 days) is done by the backend's nightly job through the Storage API,
-- because deleting rows from storage.objects does not delete the files.
