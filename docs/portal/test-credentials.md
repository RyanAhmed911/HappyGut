# Portal: test credentials for judges

The portal asks for at least one login, one row per role or user type. HappyGut has three test accounts, one per patient type. Each holds sample data only.

> **Passwords are not in this repository.** Choose three throw-away passwords, set them as `TEST_PASSWORD_NUSRAT`, `TEST_PASSWORD_RAFI` and `TEST_PASSWORD_AYESHA` in Render's **Environment** variables (and in your local `.env`), and type the same values into the portal. The portal stores them in plain text and shows them to judges and event admins, so don't reuse a password from anywhere else.

| Role / user type | Username (email) | Password | What a judge sees |
|---|---|---|---|
| Patient: Crohn's disease, in remission | `nusrat@happygut.test` | *(yours)* | Four months of records. High-fat meals, late nights and exam weeks are linked to her worse days; flare risk is raised with exams three days away. Kacchi biryani is a likely trigger because of her own history. |
| Patient: ulcerative colitis, in a flare | `rafi@happygut.test` | *(yours)* | Four months of records, eight days into a flare. Verdicts are stricter in a flare; very spicy food is his personal trigger; the index is SCCAI instead of HBI. |
| New patient: Crohn's with a stricture | `ayesha@happygut.test` | *(yours)* | No records yet: the first-day experience. The stricture safety rule already applies (leafy greens, seeds and nuts are likely triggers), and patterns appear after two weeks of diaries. |

**Suggested note for the portal's description field:**
"Sign in at the live link with any account below. Each is a different patient type with sample data. Try: Check a meal (type `kacchi biryani, borhani, firni`), fill in tonight's diary, open My patterns and My Gut, and switch on 'stricture' under Settings → Health profile to see verdicts change. Settings → Restore original records puts an account back as it was."

## Good to know
- Several judges can use the same account at once; they share its records. **Settings → Restore original records** resets one account, and restarting the backend resets all three.
- Eight wrong passwords in five minutes lock that email for five minutes.
- Set `SESSION_SECRET` on Render so a restart doesn't sign everyone out.
- Render's free service sleeps after 15 idle minutes and forgets what judges entered; a free uptime ping to `/v1/health` keeps it awake.
