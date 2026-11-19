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

### Expansion batch: fast food, snacks, drinks, desserts and fruit (2026-11-19)

**Why.** Meal checks of a burger and a pizza returned "we don't know" because every seed was a home-cooked Bangladeshi dish. This batch adds the foods people in Bangladesh commonly eat outside home cooking.

**Method.** Same as above: an LLM judge (Claude Code) estimated each component for a typical restaurant or packaged recipe sold in Bangladesh, checked the Bangla name, and chose gentler alternatives from dishes that are 🟢 in remission. No composition table was consulted. FODMAP levels for fruit follow commonly published low-FODMAP serving guidance, but no text was copied, so the source is recorded as model judgement. Not reviewed by a dietitian.

**Result.** 48 dishes added and approved (109 in total).

| Dish | Judge's note |
|---|---|
| Beef burger (`dish.beef_burger`) | A bare "burger" maps here rather than to the chicken burger: it is the more cautious reading (red-meat rule for UC). |
| Pizza (`dish.pizza`) | Lactose low: mozzarella is a low-lactose cheese. Red/processed meat low, because the common Dhaka topping is chicken; beef or pepperoni versions are higher. |
| Shawarma (`dish.shawarma`) | Fructans high: garlic sauce, wheat bread and raw onion together. |
| Pasta (`dish.pasta`) | Fructans high (wheat pasta plus garlic and onion); lactose medium for the popular white-sauce version. |
| Hot dog (`dish.hot_dog`) | Emulsifiers medium: processed sausages usually contain phosphates, binders and stabilisers. |
| Ice cream (`dish.ice_cream`) | Emulsifiers medium: mono- and diglycerides, carrageenan and gums are standard in packaged ice cream. |
| Soft drink (`dish.soft_drink`) | Sweetened with sugar (sucrose) in Bangladesh, so excess fructose none; caffeine low for colas. No current Rule Card covers sugar or carbonation, so it scores mild. |
| Milk coffee (`dish.milk_coffee`) | A bare "coffee" maps here: instant coffee with milk is the common cup. Black coffee is its own dish with caffeine high. |
| Potato chips (`dish.potato_chips`) | "Chips" means packet chips in Bangladesh; French fries are a separate dish. |
| Chanachur (`dish.chanachur`) | GOS medium from gram flour and lentils; skins/seeds/nuts medium from peanuts. |
| Salad (`dish.salad`) | Raw vegetables: insoluble fibre medium, so the stricture hard rule applies. |
| Peanuts (`dish.badam`), guava (`dish.guava`) | Skins/seeds/nuts high (whole peanuts; hard guava seeds), so the stricture hard rule applies. |
| Mango (`dish.mango`), apple (`dish.apple`), watermelon (`dish.watermelon`) | Excess fructose high; apple and watermelon also polyols high. |
| Ripe banana (`dish.banana`) | Fructans medium: ripe bananas carry more fructans than firm ones. |
| Dates (`dish.khejur`) | Fructans high, excess fructose medium for dried dates. |

**Spellings rejected in this batch** (they fit more than one dish): `soup`, `roll`, `wrap`, `bun`, `shake`, `kebab`, `kabab`, `juice`, `fruit juice`.

## Spellings (GPU job G2)

**Result.** 137 suggested spellings: 50 accepted and added to the dish aliases, 87 rejected. Every decision and its reason is in [`../g2-aliases.csv`](../g2-aliases.csv).

**Rule.** Accept a spelling only if people plausibly write this exact dish that way. Reject words that mean something else, names that fit more than one dish, and doubled-letter variants (fuzzy search already tolerates small typos).

Examples of rejections: `gur mangsho bhuna` (gur means jaggery, not beef); `বিফ থেরী` (not a real spelling); `beef theory` (not a real spelling); `begun` (means eggplant in general); `বিয়ার রোস্ট` (reads as 'beer roast'); `চাটপটি` (misspelling of চটপটি); `ডিম` (matches every egg dish); `dim` (matches every egg dish); `কলা ভুনা` (কলা means banana); `সবজি` (matches every vegetable dish); `সর্ষে মাছ` (any fish in mustard, not only hilsa); `shorshe maach` (any fish in mustard, not only hilsa).
