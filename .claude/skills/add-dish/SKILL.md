---
name: add-dish
description: Add or update a Bangladeshi dish in the HappyGut food knowledge seeds (data/seeds/dishes). Use when asked to add a dish, fix a dish's ingredients or components, or add Bangla/Banglish aliases.
---

# Add a dish to the food knowledge graph seeds

1. Check the dish isn't already there: search `data/seeds/dishes/` for its English name, Bangla name and common Banglish spellings.
2. Gather facts only from licensed sources listed in `docs/03-data.md` (Wikipedia/Wikidata, Food Composition Table for Bangladesh, USDA). Never invent composition values.
3. Write `data/seeds/dishes/<file>.yaml` (the id must be `dish.<file name>`):

```yaml
id: dish.kacchi_biryani
name_en: "Kacchi biryani"
name_bn: "কাচ্চি বিরিয়ানি"
aliases: ["kacchi", "kachchi biriyani"]      # Banglish + spelling variants; must be unique across dishes
cuisine: Bangladeshi
category: rice_dish
preparation: ["dum-cooked", "ghee", "fried onion"]
ingredients:
  - {name: "mutton"}                          # add typical_g and food_code (FCT / USDA) when known
components:                                   # list EVERY vocabulary key; levels: none | low | medium | high | unknown
  fat: high
  insoluble_fibre: low
  lactose: low
  fructans: medium
  gos: none
  polyols: none
  excess_fructose: none
  capsaicin_spice: medium
  alcohol: none
  caffeine: none
  skins_seeds_nuts: low
  red_processed_meat: high
  emulsifiers: none
level_basis: typical_recipe_estimate          # or: composition_table
gentler_alternatives: [dish.murgir_patla_jhol, dish.plain_rice]
sources:
  - {ref: "wikipedia:en:<page>", licence: "CC BY-SA 4.0"}
needs_verification: true
reviewed_by: null
status: draft                                 # draft → approved after human review
```

4. Vocabulary (from `engine/src/happygut_engine/vocab.py`): `fat`, `insoluble_fibre`, `lactose`, `fructans`, `gos`, `polyols`, `excess_fructose`, `capsaicin_spice`, `alcohol`, `caffeine`, `skins_seeds_nuts`, `red_processed_meat`, `emulsifiers`. Use `unknown` rather than guessing; unknown lowers the verdict's confidence.
5. Every alternative must exist as its own dish file and should be 🟢 in remission.
6. Approving needs `reviewed_by` and at least one source. Run `cd pipelines && uv run python -m happygut_pipelines.seeds` and the tests; only `approved` dishes are loaded.
