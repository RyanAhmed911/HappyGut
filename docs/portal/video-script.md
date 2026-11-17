# Video script: "Vibe to Production in 180 Seconds"

The guide fixes five segments and their lengths (§9.2). Stay inside each one: evaluators mark each segment on its own criterion. About 400 spoken words in total; the words below are 395.

**Before recording**
- Use the deployed app, signed in as `nusrat@happygut.test`. Language: Bangla for the demo shots (the guide checks for Bangla), English captions.
- Phone-sized screen recording for the demo; one desktop shot for My patterns.
- Put a small caption "Sample patient records" on screen during the demo segment. The guide prohibits simulated results presented as real.
- Record the voice separately and cut the screen to it. One take of the app, no mock-ups.

| Time | Guide segment (what evaluators look for) | On screen | Say |
|---|---|---|---|
| 0:00–0:30 | **Problem** (clarity, relevance) | A wedding plate: kacchi, borhani, firni. Text: "IBD: millions of people worldwide · rising fastest in newly industrialised regions" (check the exact figure and source before recording; `01-strategy.md` §6 has the references). Then a patient hesitating over the plate | "Nusrat is 27 and has Crohn's disease. At her cousin's wedding the plate is kacchi biryani, borhani and firni. Nothing has a label. Which of these will send her to bed for two days? Inflammatory bowel disease has no cure, and food triggers differ from person to person. Generic advice like 'avoid spicy food' doesn't answer the question she actually has: *is this plate a problem for me, today?*" |
| 0:30–1:00 | **Solution** (simplicity, uniqueness) | App logo → one line: "Know what your gut can take, before you eat." → the three evidence chips: guideline · what's in the food · your own diary | "HappyGut answers that question in seconds, in Bangla or English. She photographs the plate or types it, and gets a graded, explained verdict for each dish with the evidence behind it and a gentler alternative. What makes it different: the language model only reads the plate and words the answer. The verdict itself comes from a tested rules engine, and it gets more personal every night as she fills a two-minute diary." |
| 1:00–2:00 | **Demo / flow** (feasibility, logic) | 1. Check a meal: type "কাচ্চি বিরিয়ানি, বোরহানি, ফিরনি" → verdict cards (10 s). 2. Open the kacchi card: reasons, citation, "instead try" (10 s). 3. Nightly diary: foods pre-filled, tap a reaction, stool, sleep, stress, finish (15 s). 4. My patterns: graph + "High-fat meals", "Late nights", "Exam periods" (12 s). 5. My Gut: remission and flare periods on the timeline (6 s). 6. Today: flare-risk card with "Final exams start in 3 days" (7 s) | "Here it is running. Kacchi: likely trigger for her, because it is high in fat and her own diary links high-fat meals to worse days. The app shows the published guidance it relies on and suggests a lighter dish. That night, the diary already lists what she checked. She marks how her stomach was, her sleep and her stress. From those entries the Pattern Finder shows what is linked to her worse days: high-fat meals, late nights, exam weeks. It says 'linked to', never 'caused', and only after at least three occurrences. Her timeline keeps remission and flare periods apart, and with exams three days away the flare-risk card tells her why it is raised." |
| 2:00–2:30 | **AI approach** (depth, structure) | The flow diagram from the in-app "How it works" page: photo/text → perception model → food knowledge graph + cited Rule Cards → verdict engine → explanation model → output guard. Side box: PII scrub · red-flag check first | "Under the hood: a vision-language model identifies the dishes. A knowledge graph of sixty-one Bangladeshi dishes maps each to its gut-relevant components, and twenty-five rule cards carry sentences from published IBD guidance. A deterministic engine computes the verdict; a Bayesian model learns each person's patterns. Names and phone numbers are removed before any cloud call, and warning signs like heavy bleeding stop all food advice and send the user to a doctor." |
| 2:30–3:00 | **Impact and next step** (vision, potential) | Three numbers, then roadmap line, then "From Bangladesh to the world" | "We measured it. On two hundred simulated patients with hidden triggers, the Pattern Finder recovered seventy-two percent after four months of diaries. The red-flag check caught twenty-nine of twenty-nine emergency phrases in Bangla and English. Every verdict is reproducible. Next: a pilot with gastroenterology clinics in Dhaka, real diaries, and more cuisines, because adding a cuisine is adding data, not code. HappyGut: fewer surprise flares, less fear at the table." |

## Numbers you may say, and how

Source: [`../../evals/RESULTS.md`](../../evals/RESULTS.md). Say them exactly this way.

| Claim | Allowed wording | Not allowed |
|---|---|---|
| 293 of 409 hidden contributors found at 120 days | "recovered 72% of hidden triggers **in simulated patients** after four months" | "72% accurate", "predicts flares", any wording without "simulated" |
| 29 of 29 phrases, 0 of 30 false alarms | "caught 29 of 29 emergency phrases in our test set" | "100% safe", "never misses" |
| 427 of 427 identical | "every verdict is reproducible" | — |
| Knowledge | "61 Bangladeshi dishes, 25 rules with sentences from published papers, reviewed by an LLM judge" | "clinically validated", "doctor-approved" |

## Shot checklist
- [ ] Bangla UI visible in at least two shots
- [ ] "Sample patient records" caption during 1:00–2:00
- [ ] No feature shown that is not in the deployed app (no voice, no wearables, no meal-plan generation by a model)
- [ ] Final frame: team name, the five named roles, live link
- [ ] Exactly 180 seconds or just under; the same file on YouTube and Facebook
