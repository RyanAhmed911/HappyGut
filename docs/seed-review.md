# Knowledge review by the LLM judge

HappyGut is a competition prototype and the team has no clinical experts, so review is done by an **LLM judge** (Constitution IV, v2.0.0). This file is the judge's rubric. Verdicts are recorded per item in the seed files (`review:` block) and summarised in [`data/review/llm_judge/`](../data/review/llm_judge/). The app only loads items with `status: approved`.

**What this review is not:** it is not a clinical or dietetic review. Say "reviewed by an LLM judge against published sources" wherever review is described.

Check progress at any time:
```bash
cd pipelines && uv run python -m happygut_pipelines.seeds    # counts + problems
uv run --group dev pytest -q                                  # seed + engine sanity tests
```

## Rule Cards (`data/seeds/rule_cards/`)
For each card the judge must:
1. **Confirm the paper exists.** Look each citation up (Europe PMC or NCBI) and record its DOI and PMID. A citation that can't be found is removed.
2. **Retrieve supporting text.** Use the paper's full text when it is open access, otherwise its published abstract, or an open-access (CC BY) paper that reports the same guidance. Record where it came from and its licence.
3. **Quote exactly.** Copy the supporting sentence word for word (reference markers such as "[12]" may be dropped). Never write a quote from memory.
4. **Compare the claim with the quote** and record one of:
   - *direct*: the quote states the card's claim
   - *class level*: the quote supports the group the card belongs to (for example the low-FODMAP diet as a whole)
   - *partial*: the quote supports a stronger or more general form and the card applies it mildly
5. **Reword or reject.** If the card says more than the retrieved text, reword it down to what is supported. If nothing supports it, leave it `draft`.
6. **Check the wording:** no "safe", no medication advice, no "caused"; `patient_reported` cards stay mild (severity ≤ 2) and say "report" or "often".
7. **Check the Bangla** (`title_bn`, `recommendation_bn`): same meaning as the English, natural phrasing, same banned-wording rules.
8. Set `reviewed_by: llm-judge`, fill the `review:` block (date, verdict, support, note) and set `status: approved`.

Hard rules (`RC-STRICT-*`) are the safety rules: they need a quote that names strictures.

## Dishes (`data/seeds/dishes/`)
For each dish the judge:
1. Compares the ingredient list with every component level for a typical home or restaurant recipe, and corrects levels that don't fit. When unsure, `unknown` beats a guess.
2. Checks the Bangla name.
3. Checks that each gentler alternative is lower in the components that make the dish risky.
4. Records the source as `llm-judge:typical-recipe` (a model judgement, no external text copied) unless a licensed composition source was actually consulted.

## Spellings (`data/review/g2-aliases.csv`)
The local model suggests extra spellings. The judge accepts a spelling only if people plausibly write **this exact dish** that way, and rejects words that mean something else (`gur mangsho bhuna`: *gur* is jaggery; `কলা ভুনা`: *কলা* is banana), names that fit more than one dish, and doubled-letter variants (fuzzy search already tolerates small typos). Every row gets a decision, `reviewer: llm-judge` and a reason; then:
```bash
cd pipelines && uv run python -m happygut_pipelines.aliases apply
```

## Bangla interface text
`apps/web/src/locales/bn.json` and `services/api/src/happygut_api/locales/bn.json`: same meaning as the English, natural phrasing, the same placeholders, none of the banned words. Automated tests check keys, placeholders and banned words; the judge checks meaning and tone.

## Current state (2026-11-15)
| What | Result | Report |
|---|---|---|
| Rule Cards | 25 approved (7 with edits), each with an exact retrieved quote | [`rule_cards.md`](../data/review/llm_judge/rule_cards.md), [`evidence.json`](../data/review/llm_judge/evidence.json) |
| Dishes | 61 approved (3 with edits) | [`dishes.md`](../data/review/llm_judge/dishes.md) |
| Spellings | 50 accepted, 87 rejected | [`g2-aliases.csv`](../data/review/g2-aliases.csv) |
| Bangla text | reviewed | [`bangla.md`](../data/review/llm_judge/bangla.md) |
