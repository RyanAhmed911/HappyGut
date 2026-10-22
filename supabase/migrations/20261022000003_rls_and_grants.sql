-- HappyGut: row-level security and grants.
-- Every table has RLS on. Patients only see their own rows; knowledge tables are read-only for
-- signed-in users (approved items only); audit, cache and corpus chunks are backend-only.
-- service_role bypasses RLS (backend). These schemas are not added to the Data API.

-- Enable RLS everywhere
alter table knowledge.sources        enable row level security;
alter table knowledge.dishes         enable row level security;
alter table knowledge.dish_names     enable row level security;
alter table knowledge.rule_cards     enable row level security;
alter table knowledge.chunks         enable row level security;
alter table core.patients            enable row level security;
alter table core.medications         enable row level security;
alter table events.meal_checks       enable row level security;
alter table events.checkins          enable row level security;
alter table events.verdict_feedback  enable row level security;
alter table events.red_flag_events   enable row level security;
alter table audit.consents           enable row level security;
alter table audit.access_log         enable row level security;
alter table audit.model_runs         enable row level security;
alter table cache.llm_cache          enable row level security;

-- Helper: is this patient row owned by the signed-in user?
create function core.owns_patient(p_patient_id uuid) returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from core.patients p where p.id = p_patient_id and p.user_id = auth.uid()
  )
$$;
revoke all on function core.owns_patient(uuid) from public;
grant execute on function core.owns_patient(uuid) to authenticated, service_role;

-- Knowledge: approved items readable by signed-in users
create policy "read approved dishes" on knowledge.dishes
  for select to authenticated using (status = 'approved');
create policy "read names of approved dishes" on knowledge.dish_names
  for select to authenticated using (
    exists (select 1 from knowledge.dishes d where d.id = dish_id and d.status = 'approved'));
create policy "read approved rule cards" on knowledge.rule_cards
  for select to authenticated using (status = 'approved');
create policy "read sources" on knowledge.sources
  for select to authenticated using (true);
-- knowledge.chunks: no client policy (backend only)

-- Patient profile
create policy "own profile: read" on core.patients
  for select to authenticated using (user_id = auth.uid());
create policy "own profile: create" on core.patients
  for insert to authenticated with check (user_id = auth.uid() and not is_synthetic);
create policy "own profile: update" on core.patients
  for update to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());

-- Patient-owned rows
create policy "own medications" on core.medications
  for all to authenticated using (core.owns_patient(patient_id)) with check (core.owns_patient(patient_id));
create policy "own meal checks: read" on events.meal_checks
  for select to authenticated using (core.owns_patient(patient_id));
create policy "own checkins" on events.checkins
  for all to authenticated using (core.owns_patient(patient_id)) with check (core.owns_patient(patient_id));
create policy "own feedback" on events.verdict_feedback
  for all to authenticated using (core.owns_patient(patient_id)) with check (core.owns_patient(patient_id));
create policy "own red flags: read" on events.red_flag_events
  for select to authenticated using (core.owns_patient(patient_id));
create policy "own consents: read" on audit.consents
  for select to authenticated using (core.owns_patient(patient_id));
create policy "own consents: grant" on audit.consents
  for insert to authenticated with check (core.owns_patient(patient_id));
create policy "own consents: revoke" on audit.consents
  for update to authenticated using (core.owns_patient(patient_id)) with check (core.owns_patient(patient_id));
-- meal_checks and red_flag_events are written by the backend only (verdicts come from the engine).
-- access_log, model_runs, llm_cache: no client policy (backend only).

-- Grants (new tables are not exposed automatically)
grant usage on schema knowledge, core, events, audit to authenticated;
grant select on knowledge.dishes, knowledge.dish_names, knowledge.rule_cards, knowledge.sources to authenticated;
grant select, insert, update on core.patients to authenticated;
grant select, insert, update, delete on core.medications to authenticated;
grant select on events.meal_checks, events.red_flag_events to authenticated;
grant select, insert, update on events.checkins, events.verdict_feedback to authenticated;
grant select, insert, update on audit.consents to authenticated;

grant usage on schema knowledge, core, events, audit, cache to service_role;
grant all on all tables in schema knowledge, core, events, audit, cache to service_role;
grant usage, select on all sequences in schema knowledge, audit to service_role;
