# Supabase migrations

| File | What it creates |
|---|---|
| `…0001_extensions_and_knowledge.sql` | `vector`, `pg_trgm`; knowledge tables (sources, dishes, dish names, Rule Cards, guideline chunks with HNSW + full-text indexes); licence gate trigger |
| `…0002_patients_events_audit.sql` | pseudonymous patients, medications, meal checks and check-ins (monthly partitions), feedback, red flags, consents, audit, LLM cache |
| `…0003_rls_and_grants.sql` | row-level security on every table, per-patient policies, explicit grants |
| `…0004_search_functions.sql` | `knowledge.resolve_dish` (trigram over Bangla names and English-letter spellings) and `knowledge.hybrid_search` (vector + full text, RRF) |
| `…0005_supabase_cron.sql` | supabase-only: `pg_cron` jobs (cache expiry, monthly partitions) |

## Test locally (no Supabase needed)
```bash
cd supabase/tests && npm ci && npm test      # PGlite: migrations, RLS isolation, search functions
```

## Apply to the Supabase project (Windows, from the repo root)
```powershell
$env:SUPABASE_DB_URL = (Select-String '^SUPABASE_DB_URL=(.*)' .env).Matches.Groups[1].Value
npx supabase db push --db-url $env:SUPABASE_DB_URL
```
If the CLI asks for a project config, run `npx supabase init` once (keep the existing `migrations` folder), then push again.
The app tables live in their own schemas and are **not** added to the Data API; the backend reads them with the secret key.
