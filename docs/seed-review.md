# Seed review guide (Step 1)

The knowledge seeds were drafted by Claude Code **without internet access to the papers or Wikipedia**. Nothing is used by the app until a team member reviews it and sets `status: approved`. Split the files across the team; each file takes 2–5 minutes.

Check progress at any time:
```bash
cd pipelines && uv run python -m happygut_pipelines.seeds    # counts + problems
uv run --group dev pytest -q                                  # seed + engine sanity tests
```

## Rule Cards (`data/seeds/rule_cards/`, 25 files): highest priority
For each card:
1. Open each cited paper (titles in `sources[].citation`; all are findable on PubMed / Europe PMC).
2. Find the sentence that supports the card. Copy it **exactly** into `quote`, and fill in `doi`, `pmid` and `licence`.
3. If the paper doesn't support the card as written, fix the card (component, level, state, severity) or delete it. Never keep a card without a real quote.
4. `patient_reported` cards (Limdi 2016) must stay mild (severity ≤ 2) and use "often reported" wording.
5. A native Bangla speaker checks `title_bn` and `recommendation_bn` and removes the "review needed" comment.
6. Set `reviewed_by: <your name>` and `status: approved`.

**Hard rules first:** RC-STRICT-001 and RC-STRICT-002 are the safety rules. Approve them only with a clear guideline quote.

## Dishes (`data/seeds/dishes/`, 61 files)
For each dish:
1. Check the Bangla name and add common English-letter spellings you actually see people type (e.g. "kacchi", "kachchi").
2. Check each component level against the typical home or restaurant recipe. If you're unsure, use `unknown` rather than guessing.
3. Add at least one source: the Wikipedia page (`{ref: "wikipedia:en:<Page_title>", licence: "CC BY-SA 4.0"}`) and/or the Food Composition Table for Bangladesh entry.
4. Set `reviewed_by` and `status: approved`, and delete `needs_verification` once the levels are checked.

**Demo dishes first:**
- kacchi_biryani, borhani, chicken_rezala, plain_rice, murgir_patla_jhol
- shorshe_ilish, masoor_dal, alu_bhorta, fuchka, dudh_cha

## Dish-name spellings from G2 (`data/review/g2-aliases.csv`): a native Bangla speaker, ~15 minutes
Gemma suggests extra Bangla and English-letter spellings for each dish. It is often wrong in a confident way (e.g. `gur mangsho bhuna`: *gur* is jaggery; `beef theory` for tehari), so nothing enters the seeds without a person accepting it.
1. Windows, after G2's output is pulled: `cd pipelines; uv run python -m happygut_pipelines.aliases export`
2. Open the CSV in Excel. For each row, write `yes` or `no` in **decision** and your initials in **reviewer**. Say yes only if you have seen people write the dish that way. `votes` (e.g. 3/3) is how often the model gave it, not proof it's right.
3. Save as CSV (UTF-8), then: `uv run python -m happygut_pipelines.aliases apply`, `uv run python -m happygut_pipelines.seeds`, and the tests.
4. Commit the CSV and the changed dish files together: the CSV is the record of who accepted each spelling. Rerun G3 next time Ubuntu is on.

## Done when
- [ ] ≥ 25 Rule Cards approved (both hard rules included)
- [ ] ≥ 50 dishes approved (all demo dishes included)
- [ ] Validator prints `OK` and the tests pass
