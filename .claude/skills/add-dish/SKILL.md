---
name: add-dish
description: Add or update a Bangladeshi dish in the HappyGut food knowledge seeds (data/seeds/dishes). Use when asked to add a dish, fix a dish's ingredients or components, or add Bangla/Banglish aliases.
---

# Add a dish to the food knowledge graph seeds

1. Check the dish isn't already there: search `data/seeds/dishes/` for its English name, Bangla name and common Banglish spellings.
2. Gather facts only from licensed sources listed in `docs/03-data.md` (Wikipedia/Wikidata, Food Composition Table for Bangladesh, USDA). Never invent composition values.
3. Write `data/seeds/dishes/<id>.yaml`:

```yaml
id: dish.kacchi_biryani            # dish.<snake_case>
name_en: Kacchi biryani
name_bn: কাচ্চি বিরিয়ানি
aliases: [kacchi, kachchi biriyani, kacchi biryani]   # Banglish + spelling variants
cuisine: Bangladeshi
preparation: [dum-cooked, ghee, fried onion]
ingredients:
  - {id: ing.mutton, typical_g: 120, food_code: "FCT:..."}
  - {id: ing.basmati_rice, typical_g: 200, food_code: "FCT:..."}
components:                        # controlled vocabulary, levels: none | low | medium | high
  fat: high
  insoluble_fibre: low
  lactose: low
  fructans: medium                 # onion, garlic
  capsaicin_spice: medium
  skins_seeds_nuts: low
gentler_alternatives: [dish.plain_rice_chicken_rezala]
sources:
  - {ref: "wikipedia:en:Kacchi_biryani", licence: "CC BY-SA 4.0"}
  - {ref: "FCT-BD-2013:...", licence: "verify"}
reviewed_by: <team member>
status: draft                      # draft → approved after human review
```

4. Component vocabulary (don't invent new keys without updating `engine/`): `fat`, `insoluble_fibre`, `lactose`, `fructans`, `gos`, `polyols`, `excess_fructose`, `capsaicin_spice`, `alcohol`, `caffeine`, `skins_seeds_nuts`.
5. Every alternative must exist as its own dish file.
6. Leave `status: draft` until a team member reviews it; only `approved` dishes are loaded into Neo4j.
