-- HappyGut: patient profile, events (partitioned by month), consent and audit, LLM cache.
-- Patients are pseudonymous: identity stays in auth.users.

create schema if not exists core;
create schema if not exists events;
create schema if not exists audit;
create schema if not exists cache;

create table core.patients (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null unique references auth.users (id) on delete cascade,
  diagnosis    text not null check (diagnosis in ('CD', 'UC')),
  phenotypes   text[] not null default '{}',
  state        text not null default 'remission' check (state in ('remission', 'flare')),
  language     text not null default 'bn' check (language in ('bn', 'en')),
  is_synthetic boolean not null default false,
  created_at   timestamptz not null default now()
);

create table core.medications (
  id           uuid primary key default gen_random_uuid(),
  patient_id   uuid not null references core.patients (id) on delete cascade,
  name         text not null,
  generic_name text,
  schedule     jsonb not null default '{}',     -- e.g. {"times": ["08:00", "20:00"]}
  active       boolean not null default true,
  created_at   timestamptz not null default now()
);

create table events.meal_checks (
  id               uuid not null default gen_random_uuid(),
  patient_id       uuid not null references core.patients (id) on delete cascade,
  created_at       timestamptz not null default now(),
  input_type       text not null check (input_type in ('photo', 'text')),
  input_text       text,                        -- PII-scrubbed only
  image_path       text,                        -- Supabase Storage path; EXIF stripped
  dishes           jsonb not null default '[]',
  verdict          text not null check (verdict in ('likely_ok', 'caution', 'likely_trigger', 'not_sure')),
  risk             numeric(5, 4),
  confidence       numeric(5, 4),
  evidence_ids     text[] not null default '{}',
  explanation      jsonb,
  engine_version   text not null,
  model_versions   jsonb not null default '{}',
  prompt_versions  jsonb not null default '{}',
  is_synthetic     boolean not null default false,
  primary key (id, created_at)
) partition by range (created_at);
create index meal_checks_patient_time on events.meal_checks (patient_id, created_at desc);
create index meal_checks_dishes on events.meal_checks using gin (dishes);

create table events.checkins (
  id              uuid not null default gen_random_uuid(),
  patient_id      uuid not null references core.patients (id) on delete cascade,
  day             date not null,
  items           jsonb not null,               -- HBI / SCCAI answers
  index_name      text not null check (index_name in ('HBI', 'SCCAI')),
  index_score     numeric(5, 1) check (index_score >= 0),
  weight_kg       numeric(5, 1) check (weight_kg between 20 and 250),
  stress          smallint check (stress between 0 and 10),
  sleep_hours     numeric(3, 1) check (sleep_hours between 0 and 24),
  doses_taken     smallint check (doses_taken >= 0),
  doses_scheduled smallint check (doses_scheduled >= 0),
  is_synthetic    boolean not null default false,
  created_at      timestamptz not null default now(),
  primary key (id, day),
  unique (patient_id, day)
) partition by range (day);

create table events.verdict_feedback (
  id                    uuid primary key default gen_random_uuid(),
  meal_check_id         uuid not null,
  meal_check_created_at timestamptz not null,
  patient_id            uuid not null references core.patients (id) on delete cascade,
  answer                text not null check (answer in ('right', 'wrong', 'not_sure')),
  created_at            timestamptz not null default now(),
  foreign key (meal_check_id, meal_check_created_at)
    references events.meal_checks (id, created_at) on delete cascade
);

create table events.red_flag_events (
  id         uuid primary key default gen_random_uuid(),
  patient_id uuid not null references core.patients (id) on delete cascade,
  categories text[] not null,
  resolved   boolean not null default false,
  created_at timestamptz not null default now()
);
create index red_flags_unresolved on events.red_flag_events (patient_id, created_at desc) where not resolved;

create table audit.consents (
  id         uuid primary key default gen_random_uuid(),
  patient_id uuid not null references core.patients (id) on delete cascade,
  scope      text not null check (scope in ('care', 'clinician_share', 'research_aggregate')),
  granted_at timestamptz not null default now(),
  revoked_at timestamptz
);
create unique index consents_active on audit.consents (patient_id, scope) where revoked_at is null;

create table audit.access_log (
  id         bigint generated always as identity primary key,
  actor      text not null,                     -- 'patient', 'clinician:<token id>', 'service'
  patient_id uuid,
  action     text not null,
  detail     jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create table audit.model_runs (
  id             bigint generated always as identity primary key,
  purpose        text not null,                 -- 'perception', 'explanation', 'gpu_job:g1', ...
  model          text not null,
  prompt_version text,
  input_tokens   integer,
  output_tokens  integer,
  latency_ms     integer,
  created_at     timestamptz not null default now()
);

create table cache.llm_cache (
  key        text primary key,                  -- sha256 of image or prompt
  value      jsonb not null,
  model      text not null,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null
);
create index llm_cache_expiry on cache.llm_cache (expires_at);

-- Monthly partitions: a default partition catches anything outside the created ranges.
create table events.meal_checks_default partition of events.meal_checks default;
create table events.checkins_default partition of events.checkins default;

create function events.ensure_partitions(months_ahead integer default 2) returns void
language plpgsql set search_path = '' as $$
declare
  first_month date := date_trunc('month', now())::date;
  m date;
begin
  for i in 0..months_ahead loop
    m := (first_month + make_interval(months => i))::date;
    execute format(
      'create table if not exists events.%I partition of events.meal_checks for values from (%L) to (%L)',
      'meal_checks_' || to_char(m, 'YYYY_MM'), m, (m + interval '1 month')::date);
    execute format(
      'create table if not exists events.%I partition of events.checkins for values from (%L) to (%L)',
      'checkins_' || to_char(m, 'YYYY_MM'), m, (m + interval '1 month')::date);
  end loop;
end $$;

select events.ensure_partitions(3);
