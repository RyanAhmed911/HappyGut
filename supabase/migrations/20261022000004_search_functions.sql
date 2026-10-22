-- HappyGut: retrieval functions used by the meal check.

-- Dish resolution: fuzzy trigram match over English, Bangla and Banglish names.
-- Handles misspellings ("kachchi") and names inside a sentence ("ajke kacchi khabo").
create function knowledge.resolve_dish(query text, max_results integer default 5)
returns table (dish_id text, matched_name text, score real)
language sql stable set search_path = knowledge, extensions, pg_catalog as $$
  with q as (select lower(regexp_replace(normalize(trim(query), NFC), '\s+', ' ', 'g')) as nq),
  matches as (
    select dn.dish_id, dn.name,
           greatest(similarity(dn.normalized, q.nq), word_similarity(dn.normalized, q.nq)) as score
    from knowledge.dish_names dn
    join knowledge.dishes d on d.id = dn.dish_id and d.status = 'approved'
    cross join q
    where dn.normalized = q.nq or dn.normalized % q.nq or dn.normalized <% q.nq
  ),
  best as (
    select distinct on (m.dish_id) m.dish_id, m.name, m.score
    from matches m
    order by m.dish_id, m.score desc
  )
  select b.dish_id, b.name, b.score::real from best b order by b.score desc, b.dish_id limit max_results
$$;

-- Contextual hybrid search over guideline chunks: vector (cosine) + full text, fused with
-- Reciprocal Rank Fusion. The backend reranks the result with bge-reranker-v2-m3.
create function knowledge.hybrid_search(
  query_embedding extensions.vector(1024),
  query_text      text,
  match_count     integer default 5,
  candidate_count integer default 50,
  rrf_k           integer default 60,
  source_keys     text[] default null
)
returns table (
  chunk_id text, source_key text, section text, text text, context_header text, licence text,
  vector_rank integer, keyword_rank integer, rrf_score double precision
)
language sql stable set search_path = knowledge, extensions, pg_catalog as $$
  with vec as (
    select c.id, (row_number() over (order by c.embedding <=> query_embedding))::integer as r
    from knowledge.chunks c
    where c.embedding is not null and (source_keys is null or c.source_key = any (source_keys))
    order by c.embedding <=> query_embedding
    limit candidate_count
  ),
  kw as (
    select c.id, (row_number() over (order by ts_rank_cd(c.tsv, q) desc))::integer as r
    from knowledge.chunks c, websearch_to_tsquery('english', coalesce(query_text, '')) q
    where c.tsv @@ q and (source_keys is null or c.source_key = any (source_keys))
    order by ts_rank_cd(c.tsv, q) desc
    limit candidate_count
  ),
  fused as (
    select coalesce(vec.id, kw.id) as id, vec.r as vr, kw.r as kr,
           coalesce(1.0 / (rrf_k + vec.r), 0) + coalesce(1.0 / (rrf_k + kw.r), 0) as score
    from vec full outer join kw on vec.id = kw.id
  )
  select c.id, c.source_key, c.section, c.text, c.context_header, c.licence, f.vr, f.kr, f.score::double precision
  from fused f join knowledge.chunks c on c.id = f.id
  order by f.score desc, c.id
  limit match_count
$$;

grant execute on function knowledge.resolve_dish(text, integer) to authenticated, service_role;
grant execute on function knowledge.hybrid_search(extensions.vector, text, integer, integer, integer, text[]) to service_role;
