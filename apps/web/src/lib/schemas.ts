import { z } from "zod";

export const VerdictCode = z.enum(["likely_ok", "caution", "likely_trigger", "not_sure"]);
export type VerdictCode = z.infer<typeof VerdictCode>;

export const Citation = z.looseObject({
  id: z.string(),
  type: z.enum(["composition", "guideline", "personal"]),
  title: z.string().optional(),
  recommendation: z.string().optional(),
  strict_rule: z.boolean().optional(),
  sources: z.array(z.string()).optional(),
  component: z.string().optional(),
  components: z.array(z.object({ component: z.string(), level: z.string() })).optional(),
  exposures: z.number().optional(),
  probability: z.number().optional(),
  tolerated: z.boolean().optional(),
});
export type Citation = z.infer<typeof Citation>;

export const DishVerdict = z.object({
  dish_id: z.string().nullable(),
  name: z.string(),
  perceived_name: z.string(),
  verdict: VerdictCode,
  risk: z.number(),
  confidence: z.number(),
  reason: z.string(),
  contributions: z.object({ guideline: z.number(), personal: z.number() }),
  components: z.array(
    z.object({
      component: z.string(),
      level: z.string(),
      risk: z.number(),
      guideline: z.number(),
      personal: z.number(),
      rule_ids: z.array(z.string()),
      tolerated: z.boolean(),
    }),
  ),
  evidence_ids: z.array(z.string()),
  alternative: z.object({ dish_id: z.string(), name: z.string().nullable() }).nullable(),
});
export type DishVerdict = z.infer<typeof DishVerdict>;

export const DishesEvent = z.object({
  dishes: z.array(z.object({ dish_id: z.string().nullable(), name: z.string(), resolved: z.boolean() })),
});
export const VerdictEvent = z.object({
  verdict: VerdictCode,
  risk: z.number(),
  confidence: z.number(),
  engine_version: z.string(),
  dishes: z.array(DishVerdict),
  clarifying_question: z.string().nullable().optional(),
  note: z.string().optional(),
});
export type VerdictEvent = z.infer<typeof VerdictEvent>;

export const ExplanationEvent = z.object({
  dishes: z.array(
    z.object({ dish_id: z.string().nullable(), text: z.string(), cited_ids: z.array(z.string()), citations: z.array(Citation) }),
  ),
  summary: z.string(),
  source: z.string(),
  clarifying_question: z.string().nullable().optional(),
});
export type ExplanationEvent = z.infer<typeof ExplanationEvent>;

export const RedFlag = z.object({
  categories: z.array(z.string()),
  title: z.string(),
  message: z.string(),
  reasons: z.array(z.string()),
});
export type RedFlag = z.infer<typeof RedFlag>;

export const MealCheck = z.object({
  id: z.string(),
  created_at: z.string(),
  input_type: z.enum(["photo", "text"]),
  dishes: z.array(DishVerdict),
  verdict: VerdictCode,
  risk: z.number(),
  confidence: z.number(),
  explanation: ExplanationEvent,
  engine_version: z.string(),
  is_synthetic: z.boolean(),
});
export type MealCheck = z.infer<typeof MealCheck>;

export const Profile = z.object({
  id: z.string(),
  display_name: z.string(),
  diagnosis: z.enum(["CD", "UC"]),
  phenotypes: z.array(z.string()),
  state: z.enum(["remission", "flare"]),
  language: z.enum(["bn", "en"]),
  reminder_time: z.string(),
  is_synthetic: z.boolean(),
});
export type Profile = z.infer<typeof Profile>;

export const Health = z.object({
  status: z.string(),
  demo_mode: z.boolean(),
  sign_in: z.boolean().optional(),
  knowledge: z.object({ dishes: z.number(), rule_cards: z.number(), reviewed_only: z.boolean() }),
  models: z.object({ perception: z.boolean(), explanation: z.boolean() }),
});
export type Health = z.infer<typeof Health>;

// ---------------------------------------------------------------- diary

export const TIMES_OF_DAY = ["morning", "noon", "afternoon", "evening", "night"] as const;
export const REACTIONS = ["stomach_ache", "bloating", "urgency", "nausea"] as const;
export const PERIOD_TYPES = ["exam", "work", "family", "fasting", "travel", "menstruation", "other"] as const;

export const DiaryFood = z.object({
  id: z.string().optional(),
  name: z.string(),
  name_bn: z.string().nullable().optional(),
  dish_id: z.string().nullable().optional(),
  time_of_day: z.enum(TIMES_OF_DAY),
  time: z.string().nullable().optional(),
  source: z.enum(["meal_check", "diary"]),
  meal_check_id: z.string().nullable().optional(),
  reactions: z.array(z.enum(REACTIONS)),
});
export type DiaryFood = z.infer<typeof DiaryFood>;

export const DiaryAdded = z.object({ day: z.string(), added: z.number(), already: z.boolean() });
export type DiaryAdded = z.infer<typeof DiaryAdded>;

export const DiaryBody = z.object({
  foods: z.array(DiaryFood),
  stool: z.object({
    count: z.number(),
    night_count: z.number(),
    bristol: z.number().nullable(),
    blood: z.enum(["none", "streaks", "a_lot"]),
    mucus: z.boolean(),
    urgency: z.enum(["none", "hurry", "immediately", "incontinence"]),
  }),
  pain: z.number(),
  wellbeing: z.number(),
  medication: z.enum(["taken", "missed", "na"]),
  notes: z.string(),
  sleep: z.object({
    bedtime: z.string().nullable(),
    wake_time: z.string().nullable(),
    quality: z.enum(["good", "ok", "poor"]).nullable(),
  }),
  stress: z.number().nullable(),
  signs: z.object({
    fever: z.boolean(),
    vomiting: z.boolean(),
    no_stool_or_gas: z.boolean(),
    dizzy_or_little_urine: z.boolean(),
  }),
});
export type DiaryBody = z.infer<typeof DiaryBody>;

export const DiaryEntry = DiaryBody.extend({
  day: z.string(),
  completed_late: z.boolean(),
  index: z.object({ name: z.string(), score: z.number(), parts: z.record(z.string(), z.number()) }),
  sleep_hours: z.number().nullable(),
  late_night: z.boolean().nullable(),
  red_flags: z.array(z.string()),
  is_synthetic: z.boolean(),
});
export type DiaryEntry = z.infer<typeof DiaryEntry>;

export const StressPeriod = z.object({
  id: z.string(),
  type: z.enum(PERIOD_TYPES),
  name: z.string(),
  start: z.string(),
  end: z.string(),
});
export type StressPeriod = z.infer<typeof StressPeriod>;

export const DiaryDay = z.object({
  date: z.string(),
  today: z.string(),
  editable: z.boolean(),
  entry: DiaryEntry.nullable(),
  prefill: z.array(DiaryFood),
  usual: z.object({ index: z.number().nullable(), bedtime: z.string().nullable(), medication: z.string() }),
  tags: z.array(StressPeriod),
  doses: z.object({ due: z.number(), taken: z.number() }).nullable().optional(),
});
export type DiaryDay = z.infer<typeof DiaryDay>;

export const DiarySaved = z.object({
  entry: DiaryEntry,
  red_flag: RedFlag.nullable(),
  comparison: z.object({ usual: z.number(), delta: z.number(), days: z.number() }).nullable(),
});
export type DiarySaved = z.infer<typeof DiarySaved>;

export const DaySummary = z.object({
  date: z.string(),
  index: z.number(),
  stools: z.number(),
  pain: z.number(),
  sleep_hours: z.number().nullable(),
  late_night: z.boolean().nullable(),
  stress: z.number().nullable(),
  medication: z.string(),
  period_kind: z.string().nullable(),
  tags: z.array(z.string()),
  food_reaction: z.boolean(),
});
export type DaySummary = z.infer<typeof DaySummary>;
export const Days = z.object({ days: z.array(DaySummary), today: z.string(), is_synthetic: z.boolean() });

// ---------------------------------------------------------------- insights

export const PatternLabel = z.enum(["likely_contributor", "possible", "not_linked", "not_enough_data"]);
export type PatternLabel = z.infer<typeof PatternLabel>;

export const Pattern = z.object({
  factor: z.string(),
  group: z.string(),
  label: PatternLabel,
  exposures: z.number(),
  hits: z.number(),
  baseline_days: z.number(),
  baseline_hits: z.number(),
  exposed_rate: z.number(),
  baseline_rate: z.number(),
  probability: z.number(),
  window_days: z.array(z.number()),
  overlaps_with: z.array(z.string()),
  avg_index_exposed: z.number().nullable(),
  avg_index_unexposed: z.number().nullable(),
});
export type Pattern = z.infer<typeof Pattern>;

export const Patterns = z.object({
  scope: z.string(),
  days_logged: z.number(),
  min_days: z.number(),
  enough_data: z.boolean(),
  index_name: z.string(),
  results: z.array(Pattern),
  is_synthetic: z.boolean(),
});
export type Patterns = z.infer<typeof Patterns>;

export const Period = z.object({
  kind: z.enum(["remission", "flare", "settling"]),
  start: z.string(),
  end: z.string(),
  days: z.number(),
  source: z.string(),
  ongoing: z.boolean(),
  status: z.enum(["confirmed", "pending"]),
});
export type Period = z.infer<typeof Period>;

export const PeriodSummary = z.object({
  days: z.number(),
  periods: z.number(),
  avg_index: z.number().optional(),
  worst_index: z.number().optional(),
  avg_stools: z.number().optional(),
  days_with_blood: z.number().optional(),
  avg_pain: z.number().optional(),
  avg_sleep_hours: z.number().nullable().optional(),
  late_nights: z.number().optional(),
  patterns_available: z.boolean().optional(),
});
export type PeriodSummary = z.infer<typeof PeriodSummary>;

export const Periods = z.object({
  index_name: z.string(),
  thresholds: z.object({ active_at: z.number(), remission_below: z.number() }),
  rules: z.object({ window_days: z.number(), active_days_needed: z.number(), calm_days_to_end: z.number() }),
  days_logged: z.number(),
  min_days: z.number(),
  periods: z.array(Period),
  pending: z.array(Period),
  current_kind: z.string().nullable(),
  current_state: z.enum(["remission", "flare"]),
  summaries: z.object({ remission: PeriodSummary, flare: PeriodSummary }),
  before_flares: z.array(
    z.object({
      flare_start: z.string(),
      days_logged: z.number(),
      factors: z.array(z.object({ factor: z.string(), count: z.number() })),
    }),
  ),
  is_synthetic: z.boolean(),
});
export type Periods = z.infer<typeof Periods>;

export const RiskDriver = z.object({
  code: z.enum(["index_trend", "factor", "upcoming_period", "missed_doses", "in_flare"]),
  points: z.number(),
  factor: z.string().nullable(),
  count: z.number().nullable(),
  value: z.number().nullable(),
});
export type RiskDriver = z.infer<typeof RiskDriver>;

export const Risk = z.object({
  score: z.number(),
  level: z.enum(["low", "raised", "high"]),
  horizon_days: z.number(),
  enough_data: z.boolean(),
  drivers: z.array(RiskDriver),
  upcoming_periods: z.array(
    z.object({ id: z.string(), type: z.string(), name: z.string(), start: z.string(), end: z.string(), days_until: z.number() }),
  ),
  /** The machine-learning estimate (v1), shown next to the rule-based score; null when the model isn't installed. */
  model: z
    .object({
      version: z.string(),
      in_flare: z.boolean(),
      enough_data: z.boolean().optional(),
      probability: z.number().optional(),
      level: z.enum(["low", "raised", "high"]).optional(),
      drivers: z.array(z.object({ feature: z.string(), value: z.number().nullable(), effect: z.number() })).optional(),
      trained_on: z.string().optional(),
      test_roc_auc: z.number().nullable().optional(),
      v0_test_roc_auc: z.number().nullable().optional(),
      scale_checked: z.boolean().optional(),
    })
    .nullable()
    .optional(),
  is_synthetic: z.boolean(),
});
export type Risk = z.infer<typeof Risk>;

export const Report = z.object({
  generated_at: z.string(),
  from: z.string(),
  to: z.string(),
  patient: z.object({
    display_name: z.string(),
    diagnosis: z.string(),
    phenotypes: z.array(z.string()),
    current_state: z.string(),
  }),
  index_name: z.string(),
  days_logged: z.number(),
  days_in_range: z.number(),
  series: z.array(z.object({ date: z.string(), index: z.number() })),
  avg_index: z.number().nullable(),
  worst_index: z.number().nullable(),
  days_with_blood: z.number(),
  adherence: z.object({ taken: z.number(), missed: z.number(), logged: z.number() }),
  periods: z.array(Period),
  contributors: z.array(Pattern),
  risk: Risk,
  meal_verdicts: z.record(z.string(), z.number()),
  weight: z
    .object({
      latest: z.object({ date: z.string(), kg: z.number() }),
      first_in_range: z.object({ date: z.string(), kg: z.number() }).nullable(),
      weigh_ins: z.number(),
      changes: z.array(z.object({ days: z.number(), since: z.string(), from_kg: z.number(), kg: z.number(), percent: z.number() })),
      loss: z
        .object({
          level: z.enum(["notable", "larger"]),
          window: z.enum(["recent", "long"]),
          peak: z.object({ date: z.string(), kg: z.number() }),
          kg: z.number(),
          percent: z.number(),
        })
        .nullable(),
    })
    .nullable()
    .optional(),
  medications: z.array(z.object({ name: z.string(), times: z.array(z.string()), every_days: z.number(), note: z.string() })).optional(),
  appointments: z.array(z.lazy(() => Appointment)).optional(),
  is_synthetic: z.boolean(),
});
export type Report = z.infer<typeof Report>;

// ---------------------------------------------------------------- medicines and tests

export const EVERY_DAYS = [1, 7, 14, 21, 28, 42, 56] as const;
export const APPOINTMENT_KINDS = ["blood_test", "stool_test", "colonoscopy", "imaging", "doctor_visit", "other"] as const;
export const Medication = z.object({
  id: z.string(),
  name: z.string(),
  times: z.array(z.string()),
  every_days: z.number(),
  start: z.string(),
  note: z.string(),
});
export type Medication = z.infer<typeof Medication>;
export type MedicationBody = Omit<Medication, "id">;
export const Dose = z.object({ medication_id: z.string(), name: z.string(), note: z.string(), time: z.string(), taken: z.boolean() });
export type Dose = z.infer<typeof Dose>;
export const Medications = z.object({
  items: z.array(Medication),
  today: z.string(),
  day: z.object({ date: z.string(), doses: z.array(Dose) }),
});
export type Medications = z.infer<typeof Medications>;
export const Appointment = z.object({
  id: z.string(),
  kind: z.enum(APPOINTMENT_KINDS),
  date: z.string(),
  time: z.string().nullable(),
  note: z.string(),
});
export type Appointment = z.infer<typeof Appointment>;
export type AppointmentBody = Omit<Appointment, "id">;
export const Appointments = z.object({ items: z.array(Appointment), today: z.string() });

// ---------------------------------------------------------------- weight

export const WeightPoint = z.object({ date: z.string(), kg: z.number() });
export type WeightPoint = z.infer<typeof WeightPoint>;
export const WeightLoss = z.object({
  level: z.enum(["notable", "larger"]),
  window: z.enum(["recent", "long"]),
  peak: WeightPoint,
  kg: z.number(),
  percent: z.number(),
});
export type WeightLoss = z.infer<typeof WeightLoss>;
export const Weight = z.object({
  today: z.string(),
  entries: z.array(WeightPoint),
  latest: WeightPoint.nullable(),
  changes: z.array(z.object({ days: z.number(), since: z.string(), from_kg: z.number(), kg: z.number(), percent: z.number() })),
  loss: WeightLoss.nullable(),
  due: z.boolean(),
  thresholds: z.object({ recent_percent: z.number(), long_percent: z.number(), larger_percent: z.number(), min_kg: z.number(), max_kg: z.number() }),
  source: z.object({ key: z.string(), citation: z.string(), doi: z.string(), pmid: z.string(), quote: z.string(), licence: z.string() }),
  version: z.string(),
  is_synthetic: z.boolean(),
});
export type Weight = z.infer<typeof Weight>;

export const FoodMatch = z.object({ dish_id: z.string(), name_en: z.string(), name_bn: z.string(), score: z.number() });
export type FoodMatch = z.infer<typeof FoodMatch>;

export const MealCheckList = z.object({ items: z.array(MealCheck) });
export const StressPeriodList = z.object({ items: z.array(StressPeriod) });
export const FoodSearch = z.object({ results: z.array(FoodMatch) });

// ---------------------------------------------------------------- food guide and meal ideas

export const PHENOTYPES = ["stricturing", "lactose_intolerant", "ibs_like_symptoms"] as const;
export type Phenotype = (typeof PHENOTYPES)[number];

export const GuideItem = z.object({
  dish_id: z.string(),
  name_en: z.string(),
  name_bn: z.string(),
  category: z.string(),
  verdict: VerdictCode,
  risk: z.number(),
  reason: z.string(),
  components: z.array(z.object({ component: z.string(), level: z.string(), source: z.enum(["personal", "guideline"]) })),
  alternative: z.object({ dish_id: z.string(), name_en: z.string(), name_bn: z.string() }).nullable(),
});
export type GuideItem = z.infer<typeof GuideItem>;
export const Guide = z.object({ items: z.array(GuideItem) });

const PlanDish = z.object({ dish_id: z.string(), name_en: z.string(), name_bn: z.string() });
export const MealPlan = z.object({
  days: z.array(z.object({ date: z.string(), meals: z.object({ breakfast: z.array(PlanDish), lunch: z.array(PlanDish), dinner: z.array(PlanDish) }) })),
  pool_size: z.number(),
  enough: z.boolean(),
  start: z.string(),
});
export type MealPlan = z.infer<typeof MealPlan>;
