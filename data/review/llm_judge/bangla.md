# LLM-judge report: Bangla interface text

Judged on 2026-11-15 by an LLM judge (Claude Code) against the rubric in [`docs/seed-review.md`](../../../docs/seed-review.md).

**Scope.** 476 strings in `apps/web/src/locales/bn.json`, 36 strings in `services/api/src/happygut_api/locales/bn.json`, and the Bangla title and recommendation of all 25 Rule Cards.

**Checks.** Same meaning as the English; natural, respectful phrasing (আপনি form); no "নিরাপদ" (safe) claims, no medication advice, no causal wording; placeholders identical to the English; numbers and dates rendered in Bangla digits by the app. Keys, placeholders and banned words are also enforced by automated tests (`apps/web/src/test/locales.test.ts`).

**Changes made by the judge.**
| Where | Before | After | Why |
|---|---|---|---|
| "My patterns" and every place "pattern" appears | ধরন | প্যাটার্ন | ধরন also means "type", which made "আমার ধরন" ambiguous |
| "Likely contributor" label | সম্ভাব্য কারণ | সম্ভবত জড়িত | কারণ means "cause"; patterns must not be presented as causes |
| Flare-risk "what is driving it" | যে কারণে | স্কোরটি যা থেকে এসেছে | same reason |
| Rule Cards reworded in English (7 cards) | — | Bangla rewritten to match | keep both languages saying the same thing |

**Limits.** Most of this text was drafted by the same kind of model that judged it, so this review catches meaning, tone and rule violations better than it catches unnatural idiom. A native speaker's read-through is still worthwhile when one is available.
