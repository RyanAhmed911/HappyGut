# LLM-judge report: dishes and spellings

Judged on 2026-11-15 by an LLM judge (Claude Code) against the rubric in [`docs/seed-review.md`](../../../docs/seed-review.md). Not reviewed by a dietitian or a native-speaker panel.

## Dishes

**Method.** For each dish the judge compared the listed ingredients with each component level (none / low / medium / high) for a typical home or restaurant recipe, checked the Bangla name, and checked that every gentler alternative is lower in the components that make the dish risky. Levels are typical-recipe estimates; no composition table was consulted (the Food Composition Table for Bangladesh is not machine-readable from this environment), so the source is recorded as model judgement.

**Result.** 61 dishes: 58 approved as written, 3 approved with edits, 0 rejected.

| Dish | Verdict | Judge's note |
|---|---|---|
| Bhapa pitha (`dish.bhapa_pitha`) | approved with edits | Fructans lowered from low to none: rice flour, date molasses and coconut are not fructan sources. |
| Borhani (`dish.borhani`) | approved | Fermented yoghurt drink: lactose kept at medium, not high. |
| Chicken rezala (`dish.chicken_rezala`) | approved | High fat confirmed (ghee, nut paste, milk), so it is not a gentle alternative to kacchi. |
| Boiled egg (`dish.dim_sheddho`) | approved with edits | Fat raised from none to low: a boiled egg has about 5 g of fat. |
| Yogurt with flattened rice (`dish.doi_chira`) | approved with edits | Fat raised from none to low: yoghurt contributes a little fat. |
| Kacchi biryani (`dish.kacchi_biryani`) | approved | High fat and red meat confirmed (mutton, ghee). In remission no general rule flags it; a learned personal trigger or a flare does. |
| Mixed vegetable curry (`dish.mixed_shobji`) | approved | Cauliflower is a polyol source; low is right for a mixed portion. |
| Chicken curry (`dish.murgir_jhol`) | approved | Takes the plain name 'মুরগির ঝোল'; the light version keeps 'পাতলা ঝোল'. |

Dishes not listed above were approved as written with no note.

## Spellings (GPU job G2)

**Result.** 137 suggested spellings: 50 accepted and added to the dish aliases, 87 rejected. Every decision and its reason is in [`../g2-aliases.csv`](../g2-aliases.csv).

**Rule.** Accept a spelling only if people plausibly write this exact dish that way. Reject words that mean something else, names that fit more than one dish, and doubled-letter variants (fuzzy search already tolerates small typos).

Examples of rejections: `gur mangsho bhuna` (gur means jaggery, not beef); `বিফ থেরী` (not a real spelling); `beef theory` (not a real spelling); `begun` (means eggplant in general); `বিয়ার রোস্ট` (reads as 'beer roast'); `চাটপটি` (misspelling of চটপটি); `ডিম` (matches every egg dish); `dim` (matches every egg dish); `কলা ভুনা` (কলা means banana); `সবজি` (matches every vegetable dish); `সর্ষে মাছ` (any fish in mustard, not only hilsa); `shorshe maach` (any fish in mustard, not only hilsa).
