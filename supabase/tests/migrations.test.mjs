import { test, before } from 'node:test'
import assert from 'node:assert/strict'
import { freshDb, asUser, vec } from './db.mjs'

const ALICE = '11111111-1111-1111-1111-111111111111'
const BOB = '22222222-2222-2222-2222-222222222222'
let db

before(async () => {
  db = await freshDb()
  await db.exec(`
    insert into auth.users (id) values ('${ALICE}'), ('${BOB}');
    insert into core.patients (id, user_id, diagnosis, phenotypes, is_synthetic) values
      ('aaaaaaaa-0000-0000-0000-000000000001', '${ALICE}', 'CD', '{stricturing}', true),
      ('bbbbbbbb-0000-0000-0000-000000000002', '${BOB}',   'UC', '{}',            true);
    insert into events.meal_checks (patient_id, input_type, verdict, engine_version, is_synthetic) values
      ('aaaaaaaa-0000-0000-0000-000000000001', 'text', 'likely_trigger', 'engine-v0.1', true),
      ('bbbbbbbb-0000-0000-0000-000000000002', 'text', 'likely_ok',      'engine-v0.1', true);
    insert into knowledge.dishes (id, name_en, name_bn, components, status) values
      ('dish.kacchi_biryani', 'Kacchi biryani', 'কাচ্চি বিরিয়ানি', '{"fat":"high"}', 'approved'),
      ('dish.masoor_dal', 'Red lentil dal', 'মসুর ডাল', '{"gos":"medium"}', 'approved'),
      ('dish.secret_draft', 'Draft dish', 'খসড়া', '{}', 'draft');
    insert into knowledge.dish_names (dish_id, name, normalized, lang) values
      ('dish.kacchi_biryani', 'Kacchi biryani', 'kacchi biryani', 'en'),
      ('dish.kacchi_biryani', 'কাচ্চি বিরিয়ানি', 'কাচ্চি বিরিয়ানি', 'bn'),
      ('dish.kacchi_biryani', 'kacchi', 'kacchi', 'banglish'),
      ('dish.masoor_dal', 'masoor dal', 'masoor dal', 'en'),
      ('dish.masoor_dal', 'dal', 'dal', 'banglish'),
      ('dish.secret_draft', 'draft dish', 'draft dish', 'en');
  `)
})

test('all migrations apply and create the expected tables', async () => {
  const { rows } = await db.query(`
    select table_schema || '.' || table_name as t from information_schema.tables
    where table_schema in ('knowledge','core','events','audit','cache') and table_type = 'BASE TABLE'
      and table_name not like '%\\_20%' and table_name not like '%\\_default'`)
  const tables = rows.map((r) => r.t)
  for (const t of ['knowledge.dishes', 'knowledge.dish_names', 'knowledge.rule_cards', 'knowledge.chunks',
    'knowledge.sources', 'core.patients', 'core.medications', 'events.verdict_feedback',
    'events.red_flag_events', 'audit.consents', 'audit.access_log', 'audit.model_runs', 'cache.llm_cache']) {
    assert.ok(tables.includes(t), `missing ${t}`)
  }
})

test('every table has row-level security enabled', async () => {
  const { rows } = await db.query(`
    select n.nspname || '.' || c.relname as t from pg_class c join pg_namespace n on n.oid = c.relnamespace
    where n.nspname in ('knowledge','core','events','audit','cache') and c.relkind in ('r','p')
      and c.relname not like '%\\_20%' and c.relname not like '%\\_default' and not c.relrowsecurity`)
  assert.deepEqual(rows, [])
})

test('monthly partitions exist for the next months', async () => {
  const { rows } = await db.query(`
    select count(*)::int as n from pg_inherits i join pg_class c on c.oid = i.inhrelid
    where c.relname like 'meal_checks_20%'`)
  assert.ok(rows[0].n >= 4)
})

test('a patient sees only their own meal checks', async () => {
  const rows = await asUser(db, ALICE, async () => (await db.query('select verdict from events.meal_checks')).rows)
  assert.deepEqual(rows, [{ verdict: 'likely_trigger' }])
})

test("a patient can't read another patient's profile", async () => {
  const rows = await asUser(db, BOB, async () => (await db.query('select diagnosis from core.patients')).rows)
  assert.deepEqual(rows, [{ diagnosis: 'UC' }])
})

test("a patient can't write meal checks (verdicts come from the backend only)", async () => {
  await assert.rejects(asUser(db, ALICE, () => db.query(`
    insert into events.meal_checks (patient_id, input_type, verdict, engine_version)
    values ('aaaaaaaa-0000-0000-0000-000000000001', 'text', 'likely_ok', 'fake')`)))
})

test("a patient can't log a check-in for someone else", async () => {
  await assert.rejects(asUser(db, ALICE, () => db.query(`
    insert into events.checkins (patient_id, day, items, index_name, index_score)
    values ('bbbbbbbb-0000-0000-0000-000000000002', current_date, '{}', 'SCCAI', 2)`)))
})

test('a patient can log their own check-in', async () => {
  await asUser(db, ALICE, () => db.query(`
    insert into events.checkins (patient_id, day, items, index_name, index_score)
    values ('aaaaaaaa-0000-0000-0000-000000000001', current_date, '{"stool":3}', 'HBI', 4)`))
  const { rows } = await db.query('select count(*)::int as n from events.checkins')
  assert.equal(rows[0].n, 1)
})

test('signed-in users see approved dishes only, and no corpus chunks', async () => {
  const dishes = await asUser(db, ALICE, async () => (await db.query('select id from knowledge.dishes order by id')).rows)
  assert.deepEqual(dishes.map((d) => d.id), ['dish.kacchi_biryani', 'dish.masoor_dal'])
  await assert.rejects(asUser(db, ALICE, () => db.query('select * from knowledge.chunks')))
})

test('backend-only tables are closed to signed-in users', async () => {
  for (const t of ['cache.llm_cache', 'audit.model_runs', 'audit.access_log']) {
    await assert.rejects(asUser(db, ALICE, () => db.query(`select * from ${t}`)), t)
  }
})

test('licence gate blocks chunk text from sources that do not allow full text', async () => {
  await db.exec(`
    insert into knowledge.sources (key, citation, licence, full_text_allowed) values
      ('OPEN', 'Open paper', 'CC BY 4.0', true),
      ('CLOSED', 'Paywalled paper', 'all rights reserved', false);`)
  await assert.rejects(
    db.query(`insert into knowledge.chunks (id, source_key, text, licence) values ('c0', 'CLOSED', 'text', 'x')`),
    /does not allow storing full text/)
})

test('resolve_dish handles misspellings, Bangla and names inside a sentence', async () => {
  const top = async (q) => (await db.query('select * from knowledge.resolve_dish($1)', [q])).rows[0]?.dish_id
  assert.equal(await top('kachchi biriyani'), 'dish.kacchi_biryani')
  assert.equal(await top('কাচ্চি বিরিয়ানি'), 'dish.kacchi_biryani')
  assert.equal(await top('ajke dupure kacchi khabo'), 'dish.kacchi_biryani')
  assert.equal(await top('Masoor  Dal'), 'dish.masoor_dal')
  assert.equal(await top('draft dish'), undefined, 'draft dishes are never resolved')
  assert.equal(await top('pizza margherita'), undefined)
})

test('hybrid_search fuses vector and keyword ranks with RRF', async () => {
  await db.exec(`
    insert into knowledge.chunks (id, source_key, text, context_header, licence, embedding) values
      ('c1', 'OPEN', 'Patients with stricturing Crohn disease should avoid insoluble fibre.', 'ESPEN 2023, strictures', 'CC BY 4.0', '${vec(1)}'),
      ('c2', 'OPEN', 'A low FODMAP diet can reduce bloating in quiescent IBD.', 'Cox 2020, FODMAP trial', 'CC BY 4.0', '${vec(2)}'),
      ('c3', 'OPEN', 'Lactose restriction is only needed for lactose intolerance.', 'ESPEN 2023, dairy', 'CC BY 4.0', '${vec(3)}');`)
  const q = await db.query('select * from knowledge.hybrid_search($1, $2, 3)', [vec(1, 0.2), 'stricturing fibre'])
  assert.equal(q.rows[0].chunk_id, 'c1', 'the chunk matching both vector and keywords wins')
  assert.equal(q.rows[0].vector_rank, 1)
  assert.equal(q.rows[0].keyword_rank, 1)
  // c2 is the best vector match only; c3 matches the keywords (rank 1) and is 3rd by vector.
  // RRF rewards appearing in both lists, so c3 ranks above c2, and c2 is still retrieved.
  const mixed = await db.query('select * from knowledge.hybrid_search($1, $2, 3)', [vec(2), 'lactose intolerance'])
  const ids = mixed.rows.map((r) => r.chunk_id)
  assert.equal(ids[0], 'c3', 'a chunk in both lists beats a chunk in one list')
  assert.equal(mixed.rows[0].keyword_rank, 1)
  assert.ok(ids.includes('c2'), 'the best vector-only match is still retrieved')
  const c2 = mixed.rows.find((r) => r.chunk_id === 'c2')
  assert.equal(c2.vector_rank, 1)
  assert.equal(c2.keyword_rank, null)
})

test('hybrid_search is backend-only', async () => {
  await assert.rejects(asUser(db, ALICE, () => db.query('select * from knowledge.hybrid_search($1, $2)', [vec(1), 'x'])))
})
