---
name: add-rule-card
description: Turn a sentence from an IBD dietary guideline or paper into a structured, cited HappyGut Rule Card (data/seeds/rule_cards). Use when adding or reviewing guideline rules for the verdict engine.
---

# Add a Rule Card

1. The source must be in `docs/03-data.md` with a known licence. If its licence doesn't allow storing full text, the Rule Card still works: it stores our structured rule plus a short quote and the citation.
2. Copy the **exact** supporting sentence into `source.quote` first (quote-then-answer). If no sentence supports the rule, stop: no Rule Card.
3. Write `data/seeds/rule_cards/<id>.yaml`:

```yaml
id: RC-ESPEN2023-001
title_en: Limit high-fat fried foods during active disease
title_bn: <Bangla, reviewed by a native speaker>
component: fat                     # same vocabulary as dishes
min_level: high                    # rule applies at this level and above
applies_to:
  diagnosis: [CD, UC]              # CD | UC
  phenotype: [any]                 # any | stricturing | ...
  state: [flare]                   # flare | remission
severity: 2                        # 0 none · 1 mild · 2 moderate · 3 strong
hard: false                        # true = forces 🔴 (e.g. stricturing + insoluble fibre)
recommendation_en: ...
recommendation_bn: ...
source:
  citation: "Author et al. Title. Journal Year"
  doi: ""
  pmid: ""
  licence: ""
  quote: "exact sentence from the source"
reviewed_by: <team member>
status: draft                      # draft → approved
```

4. Never phrase a recommendation as "safe", and never mention medication changes.
5. `hard: true` is reserved for safety rules (stricturing Crohn's). Each hard rule needs a unit test in `engine/`.
6. Only `approved` Rule Cards are loaded.
