---
name: add-rule-card
description: Turn a sentence from an IBD dietary guideline or paper into a structured, cited HappyGut Rule Card (data/seeds/rule_cards). Use when adding or reviewing guideline rules for the verdict engine.
---

# Add a Rule Card

1. The source must be in `docs/03-data.md` with a known licence. If its licence doesn't allow storing full text, the Rule Card still works: it stores our structured rule plus a short quote and the citation.
2. Copy the **exact** supporting sentence into `source.quote` first (quote-then-answer). If no sentence supports the rule, stop: no Rule Card.
3. Write `data/seeds/rule_cards/<id>.yaml` (file name = id):

```yaml
id: RC-ESPEN2023-001
title_en: "..."
title_bn: "..."                    # native-speaker review needed
component: fat                     # same vocabulary as dishes
min_level: high                    # applies at this level and above
applies_to:
  diagnosis: [CD, UC]
  phenotype: [any]                 # any | stricturing | lactose_intolerant | ibs_like_symptoms
  state: [flare]                   # remission | flare
severity: 2                        # 0 none · 1 mild · 2 moderate · 3 strong
hard: false                        # true only for stricturing safety rules
evidence_level: guideline          # guideline | trial | clinical_practice | patient_reported
recommendation_en: "..."
recommendation_bn: "..."
sources:
  - key: ESPEN2023
    citation: "..."
    doi: ""
    pmid: ""
    licence: ""
    quote: "exact sentence from the source"
reviewed_by: null
status: draft                      # draft → approved
```

4. Never phrase a recommendation as "safe", and never mention medication (the validator rejects both).
5. `hard: true` is reserved for stricturing Crohn's safety rules, and each one needs a unit test.
6. Approving needs `reviewed_by` plus at least one source with an exact `quote` and a `licence`. Run the validator; only `approved` Rule Cards are loaded.
