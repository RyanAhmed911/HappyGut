# LLM-judge report: Rule Cards

Judged on 2026-11-15 by an LLM judge (Claude Code) against the rubric in [`docs/seed-review.md`](../../../docs/seed-review.md). Not reviewed by a clinician or dietitian.

**Method.** Each cited paper was looked up in Europe PMC to confirm it exists (DOI and PMID). None of the five originally cited papers is open access, so supporting sentences were retrieved from their published abstracts and from open-access (CC BY) papers found through Europe PMC full-text search. A card is approved only when at least one exact, retrieved sentence supports it; cards claiming more than the retrieved text were reworded. Quotes and identifiers are in [`evidence.json`](evidence.json).

**Result.** 25 cards: 18 approved as written, 7 approved with edits, 0 rejected.

| Card | Verdict | Support | Quoted sources | Judge's note |
|---|---|---|---|---|
| RC-ALCOHOL | approved | direct | LIMDI2018, MORTON2020, LIMDI2016 | Patient-reported. |
| RC-EMULSIFIERS | approved with edits | direct | GODALA2022 | Reworded to the additives named in the retrieved sentence; the earlier list (carboxymethylcellulose, polysorbate-80, carrageenan) could not be verified without the full text. |
| RC-FLARE-ALCOHOL | approved with edits | direct | GODALA2023, LIMDI2016 | Reworded to what was retrieved (avoided by 38% during active disease). |
| RC-FLARE-CAFFEINE | approved with edits | partial | GODALA2023, LIMDI2016 | Reworded: the retrieved text lists coffee among the most commonly eliminated items but is not specific to flares; the earlier 'speeds up the gut' claim had no retrieved support and was removed. |
| RC-FLARE-FAT-H | approved with edits | direct | GODALA2023, MORTON2020, LIMDI2016 | Reworded to what was retrieved: fried and fatty foods are among those most often avoided during active disease (39%). |
| RC-FLARE-FAT-M | approved | partial | GODALA2023, MORTON2020, LIMDI2016 | The evidence is about fatty and fried food; applying it mildly (severity 1) to moderately oily dishes is the card author's extension. |
| RC-FLARE-FIBRE | approved with edits | direct | GODALA2022, HASKEY2017 | Reworded to 'often recommended'. The evidence is mixed (one trial found no advantage of a low-residue diet in active Crohn's), so severity stays 1. |
| RC-FLARE-SPICE-H | approved with edits | direct | GODALA2023, LIMDI2016 | Reworded: the retrieved text reports avoidance during active disease (46%), not specific symptoms. |
| RC-FLARE-SPICE-M | approved | partial | GODALA2023, LIMDI2016 | The evidence is about spicy food in general; applying it mildly (severity 1) to moderately spicy dishes is the card author's extension. |
| RC-FLARE-SSN | approved | direct | HASKEY2017, MORTON2020 | Low-residue advice for flares plus nuts and seeds among patient-identified foods. |
| RC-FODMAP-FRUCTANS-H | approved with edits | class level | COX2020 | The trial tested the low-FODMAP diet as a whole in quiescent IBD with persistent gut symptoms; the individual FODMAP groups were not tested separately in the retrieved text. Reworded from 'reduce bloating and pain' to 'relieve gut symptoms', which is what the trial reports. |
| RC-FODMAP-FRUCTANS-M | approved | class level | COX2020 | The trial tested the low-FODMAP diet as a whole in quiescent IBD with persistent gut symptoms; the individual FODMAP groups were not tested separately in the retrieved text. |
| RC-FODMAP-FRUCTOSE | approved | class level | COX2020 | The trial tested the low-FODMAP diet as a whole in quiescent IBD with persistent gut symptoms; the individual FODMAP groups were not tested separately in the retrieved text. |
| RC-FODMAP-GOS-H | approved | class level | COX2020 | The trial tested the low-FODMAP diet as a whole in quiescent IBD with persistent gut symptoms; the individual FODMAP groups were not tested separately in the retrieved text. |
| RC-FODMAP-GOS-M | approved | class level | COX2020 | The trial tested the low-FODMAP diet as a whole in quiescent IBD with persistent gut symptoms; the individual FODMAP groups were not tested separately in the retrieved text. |
| RC-FODMAP-LACTOSE | approved | class level | COX2020 | The trial tested the low-FODMAP diet as a whole in quiescent IBD with persistent gut symptoms; the individual FODMAP groups were not tested separately in the retrieved text. |
| RC-FODMAP-POLYOLS | approved | class level | COX2020 | The trial tested the low-FODMAP diet as a whole in quiescent IBD with persistent gut symptoms; the individual FODMAP groups were not tested separately in the retrieved text. |
| RC-LACTOSE-L | approved | direct | SOOD2019, GODALA2022 |  |
| RC-LACTOSE-M | approved | direct | GODALA2022, SOOD2019 |  |
| RC-SATFAT | approved | direct | GODALA2023 | A secondary source reporting the IOIBD guidance; the food examples (ghee, butter, dalda) are the card author's mapping. |
| RC-SPICE | approved | direct | GODALA2023, MORTON2020, LIMDI2016 | Patient-reported: spicy food is the item most often avoided in remission (39%). |
| RC-STRICT-001 | approved | direct | BARBERIO2025, AGA2024 | Both sources name fibrous plant foods and strictures. One review notes the evidence behind this long-standing advice is weak; kept as a strict rule because it errs on the side of caution. |
| RC-STRICT-002 | approved | direct | BARBERIO2025, AGA2024 | The quoted advice names peels, nuts and seeds for stricturing disease. |
| RC-STRICT-003 | approved | direct | BARBERIO2025, AGA2024 | Supports soft, well-cooked preparation for people with strictures. |
| RC-UC-REDMEAT | approved | direct | AGA2024, GODALA2023 | Applies to ulcerative colitis only, as the quotes say. |

**Support levels.** *direct*: the quote states the card's claim. *class level*: the quote supports the group the card belongs to (the low-FODMAP diet as a whole). *partial*: the quote supports a stronger or more general form and the card applies it mildly.

**Limits.** The ESPEN 2023 and IOIBD 2020 guidelines and the Limdi 2016 survey are cited by identity only (or by abstract), because their full text is not openly available. The stricture rules follow long-standing advice whose evidence base one of the quoted reviews itself calls weak; they are kept because they err on the side of caution.
