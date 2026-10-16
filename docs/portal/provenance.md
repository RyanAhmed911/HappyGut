# Portal text: Data & AI provenance (required field)

## Data sources
- Internal: Supabase app database (profiles, meal checks, verdicts, HBI/SCCAI check-ins, adherence, verdict feedback), Neo4j Personal Gut Graph, team-authored Rule Cards
- Free APIs: USDA FoodData Central (CC0), Open Food Facts (ODbL), Europe PMC (licence-filtered open access), PubMed E-utilities (citation metadata)
- Scraped / crawled: Wikipedia Bangladeshi cuisine pages, English + Bangla (CC BY-SA); open-access ESPEN, IOIBD and AGA guideline documents
- Open datasets: Food Composition Table for Bangladesh (INFS, University of Dhaka), Wikidata (CC0), published FODMAP composition tables, Google Dakshina (CC BY-SA)
- User uploads: meal / menu / label photos; ~300 team-captured Bangladeshi meal photos (test set)
- Synthetic (always labelled): simulated IBD patient cohort with injected triggers; generated Bangla/Banglish, red-flag and guideline Q&A evaluation sets
- Not used: proprietary databases (e.g. Monash FODMAP), social-media health posts, real patient records

## AI models
- Gemini Flash (free tier): meal / label vision, Bangla/English explanations, meal plans, weekly summaries
- Llama (Groq free tier + local Llama 3.2 3B): fast routing, red-flag second check, fallback explainer
- Gemma 3 4B (local, Ollama): PII scrubbing, Bangla/Banglish normalisation, vision fallback
- Qwen 2.5 7B (local): batch Rule Card extraction, dish enrichment, contextual chunk headers
- DeepSeek-R1-Distill-Qwen-7B (local): LLM-as-judge for evaluation
- BGE-M3 (fine-tuned for dish names) + bge-reranker-v2-m3: multilingual embeddings and reranking
- Custom models: LightGBM flare early-warning model (+ SHAP); Bayesian N-of-1 trigger model
- Claude (via Claude Code): development only, not at runtime

## Responsible AI
- The LLM never decides: verdicts come from a deterministic, unit-tested engine; AI only reads inputs and explains
- Graded verdicts, never "safe"; ⚪ "Not sure" when evidence is weak; every claim cites a source
- Red-flag symptoms stop diet advice and direct the user to a doctor or emergency care; no medication advice, ever
- Stricturing Crohn's safety rules applied before any AI output
- Privacy: PII stripped by a local model before any cloud call; EXIF/GPS removed; pseudonymous IDs; consent scopes; row-level security; export and delete on request
- Free-tier cloud APIs only receive food photos and de-identified text
- Bias checks: metrics broken down by language (Bangla / English / Banglish), sex and disease phenotype; native-speaker review of Bangla output
- Transparency: evidence bar, citations, SHAP factors on alerts, model/data cards, prompt and model versions logged per verdict
- Honesty: simulated-data results always labelled; no fabricated traction or outcomes
- Human oversight: humans approve AI-extracted knowledge and review every AI-generated code change
- Legally sourced data only, each source's licence recorded; positioned as self-management support, not a medical device
