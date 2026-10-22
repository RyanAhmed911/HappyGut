// Applies the Supabase migrations to an in-process Postgres (PGlite) with stand-ins for the
// Supabase pieces that PGlite doesn't have: the auth schema, auth.uid() and the API roles.
import { PGlite } from '@electric-sql/pglite'
import { vector } from '@electric-sql/pglite-pgvector'
import { pg_trgm } from '@electric-sql/pglite/contrib/pg_trgm'
import { readdirSync, readFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const MIGRATIONS = join(dirname(fileURLToPath(import.meta.url)), '..', 'migrations')

const SUPABASE_STANDINS = `
  create schema extensions;
  create role anon nologin;
  create role authenticated nologin;
  create role service_role nologin bypassrls;
  create schema auth;
  create table auth.users (id uuid primary key);
  create function auth.uid() returns uuid language sql stable as $$
    select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid
  $$;
  grant usage on schema auth to authenticated, service_role;
  grant execute on function auth.uid() to authenticated, service_role;
`

export async function freshDb() {
  const db = new PGlite({ extensions: { vector, pg_trgm } })
  await db.exec(SUPABASE_STANDINS)
  const files = readdirSync(MIGRATIONS).filter((f) => f.endsWith('.sql')).sort()
  for (const f of files) {
    const sql = readFileSync(join(MIGRATIONS, f), 'utf8')
    if (sql.startsWith('-- supabase-only')) continue
    try {
      await db.exec(sql)
    } catch (err) {
      throw new Error(`migration ${f} failed: ${err.message}`)
    }
  }
  return db
}

// Run fn as a signed-in user (role authenticated + JWT subject), then switch back.
export async function asUser(db, userId, fn) {
  await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub', '${userId}', false);`)
  try {
    return await fn()
  } finally {
    await db.exec(`reset role; select set_config('request.jwt.claim.sub', '', false);`)
  }
}

// A deterministic 1024-d unit vector pointing mostly along `axis`.
export function vec(axis, wobble = 0) {
  const v = new Array(1024).fill(0)
  v[axis] = 1
  if (wobble) v[(axis + 1) % 1024] = wobble
  const n = Math.hypot(...v)
  return '[' + v.map((x) => (x / n).toFixed(6)).join(',') + ']'
}
