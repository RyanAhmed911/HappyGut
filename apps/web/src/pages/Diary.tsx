import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Check, CircleCheck, GraduationCap, LoaderCircle, Plus, ScanLine, Search, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router";
import { LoadError, PageLoading, useLang } from "@/components/shell";
import { Badge, Button, Card, Chip, Field, inputClass, PageTitle, Segmented, Sheet, Stepper, Toggle } from "@/components/ui";
import { Escalation } from "@/components/verdict";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import { addDays, clock, longDate, num, shortDate } from "@/lib/format";
import { PERSONAL_KEYS, useToday } from "@/lib/hooks";
import { REACTIONS, TIMES_OF_DAY, type DiaryBody, type DiaryDay, type DiaryFood, type DiarySaved, type FoodMatch } from "@/lib/schemas";

const STEPS = ["food", "stool", "feel", "sleep", "review"] as const;

function initial(day: DiaryDay): DiaryBody {
  if (day.entry) {
    const { foods, stool, pain, wellbeing, medication, notes, sleep, stress, signs } = day.entry;
    return { foods: [...foods, ...day.prefill], stool, pain, wellbeing, medication, notes, sleep, stress, signs };
  }
  return {
    foods: day.prefill,
    stool: { count: 1, night_count: 0, bristol: null, blood: "none", mucus: false, urgency: "none" },
    pain: 0,
    wellbeing: 0,
    medication: day.usual.medication === "na" ? "na" : "taken",
    notes: "",
    sleep: { bedtime: day.usual.bedtime, wake_time: null, quality: null },
    stress: null,
    signs: { fever: false, vomiting: false, no_stool_or_gas: false, dizzy_or_little_urine: false },
  };
}

// ---------------------------------------------------------------- Bristol stool chart (drawn, not photographed)

function BristolShape({ type }: { type: number }) {
  const fill = "currentColor";
  const shapes: Record<number, React.ReactNode> = {
    1: [8, 20, 32, 44].map((x) => <circle key={x} cx={x} cy={12} r={4.2} fill={fill} />),
    2: [10, 18, 26, 34, 42].map((x) => <circle key={x} cx={x} cy={12} r={6} fill={fill} />),
    3: (
      <>
        <rect x={4} y={6} width={44} height={12} rx={6} fill={fill} />
        {[15, 26, 37].map((x) => (
          <path key={x} d={`M${x} 7 l-2 5 l2 5`} stroke="var(--color-card)" strokeWidth={1.4} fill="none" />
        ))}
      </>
    ),
    4: <rect x={4} y={7} width={44} height={10} rx={5} fill={fill} />,
    5: [
      [10, 11, 7, 5],
      [26, 13, 8, 5],
      [42, 11, 7, 5],
    ].map(([cx, cy, rx, ry]) => <ellipse key={cx} cx={cx} cy={cy} rx={rx} ry={ry} fill={fill} />),
    6: <path d="M5 14c2-7 7-2 10-6s6 2 9-1 6 3 9 0 7-1 9 4-3 7-8 6-7 2-11 1-8 2-11 0-9 1-7-4z" fill={fill} />,
    7: <path d="M3 13c5-4 9 3 14 0s9-4 14 0 9 3 18 0v6H3z" fill={fill} opacity={0.75} />,
  };
  return (
    <svg viewBox="0 0 52 24" className="h-7 w-14" aria-hidden>
      {shapes[type]}
    </svg>
  );
}

function BristolPicker({ value, onChange }: { value: number | null; onChange: (v: number) => void }) {
  const { t } = useTranslation();
  const lang = useLang();
  return (
    <div role="radiogroup" className="grid grid-cols-1 gap-2 sm:grid-cols-2">
      {[1, 2, 3, 4, 5, 6, 7].map((type) => (
        <button
          key={type}
          type="button"
          role="radio"
          aria-checked={value === type}
          onClick={() => onChange(type)}
          className={cn(
            "flex items-center gap-3 rounded-xl border px-3 py-2 text-left transition active:scale-[0.98]",
            value === type ? "border-brand bg-brand-tint ring-2 ring-brand/20" : "border-line bg-card hover:border-brand/40",
          )}
        >
          <span className={cn("grid h-7 w-7 shrink-0 place-items-center rounded-full text-sm font-bold", value === type ? "bg-brand text-white" : "bg-paper-deep text-ink-soft")}>
            {num(type, lang)}
          </span>
          <span className={cn(type >= 6 ? "text-caution" : type <= 2 ? "text-ink-soft" : "text-ink-soft/80")}>
            <BristolShape type={type} />
          </span>
          <span className="text-[13px] leading-snug text-ink-soft">{t(`diary.bristol_${type}`)}</span>
        </button>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------- add a food

function AddFoodSheet({ open, onOpenChange, onAdd }: { open: boolean; onOpenChange: (o: boolean) => void; onAdd: (food: DiaryFood) => void }) {
  const { t } = useTranslation();
  const lang = useLang();
  const [q, setQ] = useState("");
  const [debounced, setDebounced] = useState("");
  const [time, setTime] = useState<(typeof TIMES_OF_DAY)[number]>("noon");
  useEffect(() => {
    const id = setTimeout(() => setDebounced(q.trim()), 220);
    return () => clearTimeout(id);
  }, [q]);
  useEffect(() => {
    if (open) setQ("");
  }, [open]);
  const results = useQuery({ queryKey: ["foods", debounced], queryFn: () => api.searchFoods(debounced), enabled: debounced.length >= 2 });

  const add = (match: FoodMatch | null): void => {
    onAdd(
      match
        ? { name: match.name_en, name_bn: match.name_bn, dish_id: match.dish_id, time_of_day: time, source: "diary", reactions: [] }
        : { name: q.trim(), dish_id: null, time_of_day: time, source: "diary", reactions: [] },
    );
    onOpenChange(false);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange} title={t("diary.add_food")} description={t("diary.add_food_hint")}>
      <div className="mb-3 flex flex-wrap gap-1.5">
        {TIMES_OF_DAY.map((x) => (
          <Chip key={x} selected={time === x} className="min-h-9 px-3 text-[13px]" onClick={() => setTime(x)}>
            {t(`time.${x}`)}
          </Chip>
        ))}
      </div>
      <div className="relative">
        <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
        <input autoFocus value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("diary.food_placeholder")} className={cn(inputClass, "pl-10")} maxLength={80} />
      </div>
      <ul className="mt-3 max-h-64 space-y-1.5 overflow-y-auto">
        {results.data?.map((m) => (
          <li key={m.dish_id}>
            <button type="button" onClick={() => add(m)} className="flex w-full items-center justify-between gap-3 rounded-xl border border-line px-4 py-2.5 text-left hover:border-brand/50 hover:bg-brand-tint">
              <span>
                <span className="block font-semibold">{lang === "bn" ? m.name_bn : m.name_en}</span>
                <span className="text-xs text-ink-faint">{lang === "bn" ? m.name_en : m.name_bn}</span>
              </span>
              <Plus className="h-4 w-4 text-brand" />
            </button>
          </li>
        ))}
        {q.trim().length >= 2 && (
          <li>
            <button type="button" onClick={() => add(null)} className="flex w-full items-center justify-between gap-3 rounded-xl border border-dashed border-line px-4 py-2.5 text-left text-sm text-ink-soft hover:border-brand/50">
              <span>{t("diary.add_as_typed", { text: q.trim() })}</span>
              <Plus className="h-4 w-4" />
            </button>
          </li>
        )}
      </ul>
    </Sheet>
  );
}

function FoodRow({ food, onChange, onRemove }: { food: DiaryFood; onChange: (f: DiaryFood) => void; onRemove: () => void }) {
  const { t } = useTranslation();
  const lang = useLang();
  const name = lang === "bn" && food.name_bn ? food.name_bn : food.name;
  const toggle = (r: (typeof REACTIONS)[number]): void =>
    onChange({ ...food, reactions: food.reactions.includes(r) ? food.reactions.filter((x) => x !== r) : [...food.reactions, r] });
  return (
    <li className="rounded-xl border border-line bg-card p-3.5">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-bold leading-snug">{name}</p>
          <p className="mt-0.5 flex flex-wrap items-center gap-1.5 text-xs text-ink-faint">
            {t(`time.${food.time_of_day}`)}
            {food.source === "meal_check" && (
              <Badge tone="brand">
                <ScanLine className="h-3 w-3" />
                {t("diary.from_check")}
              </Badge>
            )}
            {!food.dish_id && <Badge>{t("diary.unknown_food")}</Badge>}
          </p>
        </div>
        <button type="button" onClick={onRemove} aria-label={t("app.remove")} className="rounded-full p-1.5 text-ink-faint hover:bg-paper-deep hover:text-trigger">
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
      <div className="mt-2.5 flex flex-wrap gap-1.5">
        {REACTIONS.map((r) => (
          <Chip
            key={r}
            selected={food.reactions.includes(r)}
            onClick={() => toggle(r)}
            className={cn("min-h-8 px-2.5 py-1 text-xs", food.reactions.includes(r) && "border-trigger bg-trigger")}
          >
            {t(`reaction.${r}`)}
          </Chip>
        ))}
      </div>
    </li>
  );
}

// ---------------------------------------------------------------- result

function Result({ saved, date, onEdit }: { saved: DiarySaved; date: string; onEdit: () => void }) {
  const { t } = useTranslation();
  const lang = useLang();
  const navigate = useNavigate();
  if (saved.red_flag) {
    return (
      <div className="mx-auto max-w-md pt-2">
        <Escalation flag={saved.red_flag} onClose={() => void navigate("/")} />
        <p className="mt-4 text-center text-sm text-ink-soft">{t("diary.saved_anyway")}</p>
      </div>
    );
  }
  const { entry, comparison } = saved;
  const delta = comparison?.delta ?? 0;
  const tone = delta >= 2 ? "trigger" : delta <= -2 ? "ok" : "brand";
  return (
    <div className="mx-auto max-w-md pt-4 text-center">
      <span className="animate-pop mx-auto grid h-16 w-16 place-items-center rounded-full bg-ok-soft text-ok">
        <CircleCheck className="h-9 w-9" />
      </span>
      <h1 className="mt-4 text-2xl font-bold">{t("diary.saved_title")}</h1>
      <p className="text-ink-soft">{longDate(date, lang)}</p>

      <Card className="animate-rise mt-6">
        <p className="text-[13px] font-bold uppercase tracking-[0.08em] text-ink-faint">{t("diary.your_score", { index: entry.index.name })}</p>
        <p className={cn("tabular mt-1 text-6xl font-bold", tone === "trigger" ? "text-trigger" : tone === "ok" ? "text-ok" : "text-brand")}>{num(entry.index.score, lang)}</p>
        <p className="mt-2 text-[15px] text-ink-soft">
          {comparison
            ? t(delta >= 2 ? "diary.cmp_higher" : delta <= -2 ? "diary.cmp_lower" : "diary.cmp_same", { usual: num(comparison.usual, lang), days: num(comparison.days, lang) })
            : t("diary.cmp_none")}
        </p>
        <div className="mt-4 flex flex-wrap justify-center gap-2 text-sm">
          {entry.sleep_hours !== null && (
            <Badge tone={entry.late_night ? "caution" : "neutral"}>
              {t("diary.slept", { hours: num(entry.sleep_hours, lang, 1) })}
              {entry.late_night ? ` · ${t("diary.late_night")}` : ""}
            </Badge>
          )}
          {entry.completed_late && <Badge>{t("diary.filled_late")}</Badge>}
          {entry.foods.some((f) => f.reactions.length) && <Badge tone="trigger">{t("diary.reaction_logged")}</Badge>}
        </div>
        <p className="mt-4 text-xs text-ink-faint">{t("diary.index_note", { index: entry.index.name })}</p>
      </Card>

      <div className="mt-5 grid gap-2.5 sm:grid-cols-2">
        <Button variant="outline" onClick={onEdit}>
          {t("diary.edit")}
        </Button>
        <Link to="/patterns" className="inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-brand px-5 text-[15px] font-semibold text-white shadow-float">
          {t("diary.see_patterns")}
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- page

export function Diary() {
  const { t } = useTranslation();
  const lang = useLang();
  const params = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const today = useToday();
  const date = params.date ?? today;
  const day = useQuery({ queryKey: ["diary", date], queryFn: () => api.diary(date!), enabled: !!date });

  const [form, setForm] = useState<DiaryBody | null>(null);
  const [step, setStep] = useState(0);
  const [adding, setAdding] = useState(false);
  const [saved, setSaved] = useState<DiarySaved | null>(null);

  useEffect(() => {
    setForm(null);
    setStep(0);
    setSaved(null);
  }, [date]);
  useEffect(() => {
    if (day.data && !form) setForm(initial(day.data));
  }, [day.data, form]);

  const save = useMutation({
    mutationFn: (body: DiaryBody) => api.saveDiary(date!, body, lang),
    onSuccess: (result) => {
      setSaved(result);
      window.scrollTo({ top: 0 });
      for (const key of PERSONAL_KEYS) void queryClient.invalidateQueries({ queryKey: [...key] });
    },
  });

  const byTime = useMemo(() => {
    const groups = new Map<string, { food: DiaryFood; index: number }[]>();
    form?.foods.forEach((food, index) => {
      const list = groups.get(food.time_of_day) ?? [];
      list.push({ food, index });
      groups.set(food.time_of_day, list);
    });
    return TIMES_OF_DAY.filter((x) => groups.has(x)).map((x) => [x, groups.get(x)!] as const);
  }, [form?.foods]);

  if (!date || day.isLoading) return <PageLoading />;
  if (day.isError || !day.data) return <LoadError onRetry={() => void day.refetch()} />;
  if (!form) return <PageLoading />;
  if (saved) return <Result saved={saved} date={date} onEdit={() => setSaved(null)} />;

  const set = <K extends keyof DiaryBody>(key: K, value: DiaryBody[K]): void => setForm({ ...form, [key]: value });
  const editable = day.data.editable;
  const dates = today ? [today, addDays(today, -1), addDays(today, -2)] : [];
  const stepName = STEPS[step]!;
  const n = (v: number): string => num(v, lang);

  return (
    <div>
      <PageTitle title={t("diary.title")} subtitle={longDate(date, lang)} />

      <div className="mb-4 flex flex-wrap gap-2">
        {dates.map((d, i) => (
          <Chip key={d} selected={d === date} className="min-h-9 text-[13px]" onClick={() => void navigate(i === 0 ? "/diary" : `/diary/${d}`)}>
            {i === 0 ? t("app.today") : i === 1 ? t("app.yesterday") : shortDate(d, lang)}
          </Chip>
        ))}
        {day.data.entry && <Badge tone="ok" className="self-center">{t("diary.already_filled")}</Badge>}
      </div>

      {day.data.tags.map((tag) => (
        <p key={tag.id} className="mb-3 flex items-center gap-2 rounded-xl bg-brand-tint px-3.5 py-2 text-sm text-brand-deep">
          <GraduationCap className="h-4 w-4 shrink-0" />
          {t("diary.tagged", { name: tag.name })}
        </p>
      ))}

      {!editable && <p className="mb-4 rounded-xl bg-unsure-soft px-4 py-3 text-sm text-unsure">{t("diary.too_late")}</p>}

      {/* Progress */}
      <ol className="mb-5 flex gap-1.5" aria-label={t("diary.progress")}>
        {STEPS.map((s, i) => (
          <li key={s} className="flex-1">
            <button type="button" onClick={() => setStep(i)} className="w-full text-left" aria-current={i === step ? "step" : undefined}>
              <span className={cn("block h-1.5 rounded-full transition", i <= step ? "bg-brand" : "bg-paper-deep")} />
              <span className={cn("mt-1.5 block truncate text-[11px] font-semibold", i === step ? "text-brand" : "text-ink-faint")}>{t(`diary.step_${s}`)}</span>
            </button>
          </li>
        ))}
      </ol>

      <fieldset disabled={!editable} className="animate-rise min-w-0" key={stepName}>
        {stepName === "food" && (
          <div>
            <h2 className="text-xl font-bold">{t("diary.q_food")}</h2>
            <p className="mb-4 mt-1 text-sm text-ink-soft">{t("diary.q_food_hint")}</p>
            {byTime.length === 0 && <p className="mb-3 rounded-xl border border-dashed border-line px-4 py-6 text-center text-sm text-ink-soft">{t("diary.no_food")}</p>}
            {byTime.map(([time, foods]) => (
              <div key={time} className="mb-3">
                <p className="mb-1.5 text-xs font-bold uppercase tracking-[0.08em] text-ink-faint">{t(`time.${time}`)}</p>
                <ul className="space-y-2">
                  {foods.map(({ food, index }) => (
                    <FoodRow
                      key={`${food.name}-${index}`}
                      food={food}
                      onChange={(f) => set("foods", form.foods.map((x, i) => (i === index ? f : x)))}
                      onRemove={() => set("foods", form.foods.filter((_, i) => i !== index))}
                    />
                  ))}
                </ul>
              </div>
            ))}
            <Button variant="secondary" className="w-full" onClick={() => setAdding(true)}>
              <Plus className="h-4 w-4" />
              {t("diary.add_food")}
            </Button>
            <AddFoodSheet open={adding} onOpenChange={setAdding} onAdd={(food) => set("foods", [...form.foods, food])} />
          </div>
        )}

        {stepName === "stool" && (
          <div>
            <h2 className="mb-4 text-xl font-bold">{t("diary.q_stool")}</h2>
            <Field label={t("diary.stool_count")}>
              <Stepper label={t("diary.stool_count")} value={form.stool.count} onChange={(v) => set("stool", { ...form.stool, count: v, night_count: Math.min(form.stool.night_count, v) })} />
            </Field>
            <Field label={t("diary.bristol")} hint={t("diary.bristol_hint")}>
              <BristolPicker value={form.stool.bristol} onChange={(v) => set("stool", { ...form.stool, bristol: v })} />
            </Field>
            <Field label={t("diary.blood")}>
              <Segmented value={form.stool.blood} onChange={(v) => set("stool", { ...form.stool, blood: v })} options={(["none", "streaks", "a_lot"] as const).map((v) => ({ value: v, label: t(`diary.blood_${v}`) }))} />
            </Field>
            <Field label={t("diary.urgency")}>
              <Segmented
                className="grid-cols-2 sm:grid-cols-4"
                value={form.stool.urgency}
                onChange={(v) => set("stool", { ...form.stool, urgency: v })}
                options={(["none", "hurry", "immediately", "incontinence"] as const).map((v) => ({ value: v, label: t(`diary.urgency_${v}`) }))}
              />
            </Field>
            <Field label={t("diary.night_stools")}>
              <Stepper label={t("diary.night_stools")} value={form.stool.night_count} max={form.stool.count} onChange={(v) => set("stool", { ...form.stool, night_count: v })} />
            </Field>
            <Toggle label={t("diary.mucus")} checked={form.stool.mucus} onChange={(v) => set("stool", { ...form.stool, mucus: v })} />
          </div>
        )}

        {stepName === "feel" && (
          <div>
            <h2 className="mb-4 text-xl font-bold">{t("diary.q_feel")}</h2>
            <Field label={t("diary.pain")}>
              <Segmented value={form.pain} onChange={(v) => set("pain", v)} options={[0, 1, 2, 3].map((v) => ({ value: v, label: t(`diary.pain_${v}`) }))} />
            </Field>
            <Field label={t("diary.wellbeing")}>
              <Segmented
                value={form.wellbeing}
                onChange={(v) => set("wellbeing", v)}
                options={[0, 1, 2, 3, 4].map((v) => ({ value: v, label: <span className="text-xl">{["😀", "🙂", "😕", "😣", "😫"][v]}</span>, hint: t(`diary.wellbeing_${v}`) }))}
              />
            </Field>
            <Field label={t("diary.medication")} hint={t("diary.medication_hint")}>
              <Segmented value={form.medication} onChange={(v) => set("medication", v)} options={(["taken", "missed", "na"] as const).map((v) => ({ value: v, label: t(`diary.med_${v}`) }))} />
            </Field>
            <Field label={t("diary.signs")} hint={t("diary.signs_hint")}>
              <div className="space-y-2">
                {(["fever", "vomiting", "no_stool_or_gas", "dizzy_or_little_urine"] as const).map((key) => (
                  <Toggle key={key} label={t(`diary.sign_${key}`)} checked={form.signs[key]} onChange={(v) => set("signs", { ...form.signs, [key]: v })} />
                ))}
              </div>
            </Field>
          </div>
        )}

        {stepName === "sleep" && (
          <div>
            <h2 className="mb-4 text-xl font-bold">{t("diary.q_sleep")}</h2>
            <div className="grid grid-cols-2 gap-3">
              <Field label={t("diary.bedtime")} hint={day.data.usual.bedtime ? t("diary.usual", { time: clock(day.data.usual.bedtime, lang) }) : undefined}>
                <input type="time" className={inputClass} value={form.sleep.bedtime ?? ""} onChange={(e) => set("sleep", { ...form.sleep, bedtime: e.target.value || null })} />
              </Field>
              <Field label={t("diary.wake_time")}>
                <input type="time" className={inputClass} value={form.sleep.wake_time ?? ""} onChange={(e) => set("sleep", { ...form.sleep, wake_time: e.target.value || null })} />
              </Field>
            </div>
            <Field label={t("diary.sleep_quality")}>
              <Segmented value={form.sleep.quality} onChange={(v) => set("sleep", { ...form.sleep, quality: v })} options={(["good", "ok", "poor"] as const).map((v) => ({ value: v, label: t(`diary.quality_${v}`) }))} />
            </Field>
            <h2 className="mb-4 mt-8 text-xl font-bold">{t("diary.q_stress")}</h2>
            <Field label={t("diary.stress")}>
              <Segmented value={form.stress} onChange={(v) => set("stress", v)} options={[0, 1, 2, 3, 4].map((v) => ({ value: v, label: n(v), hint: t(`diary.stress_${v}`) }))} />
            </Field>
            <Link to="/gut#periods" className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand">
              <GraduationCap className="h-4 w-4" />
              {t("diary.mark_period")}
            </Link>
          </div>
        )}

        {stepName === "review" && (
          <div>
            <h2 className="mb-4 text-xl font-bold">{t("diary.q_notes")}</h2>
            <textarea
              value={form.notes}
              onChange={(e) => set("notes", e.target.value)}
              rows={3}
              maxLength={500}
              placeholder={t("diary.notes_placeholder")}
              className="w-full resize-none rounded-2xl border border-line bg-card p-4 text-[15px] outline-none focus:border-brand focus:ring-4 focus:ring-brand/10"
            />
            <Card className="mt-4 p-4 text-sm">
              <p className="mb-2 text-[13px] font-bold uppercase tracking-[0.08em] text-ink-faint">{t("diary.summary")}</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-2">
                {[
                  [t("diary.sum_foods"), n(form.foods.length)],
                  [t("diary.sum_reactions"), n(form.foods.filter((f) => f.reactions.length).length)],
                  [t("diary.stool_count"), n(form.stool.count)],
                  [t("diary.bristol"), form.stool.bristol ? n(form.stool.bristol) : "–"],
                  [t("diary.pain"), t(`diary.pain_${form.pain}`)],
                  [t("diary.medication"), t(`diary.med_${form.medication}`)],
                  [t("diary.bedtime"), form.sleep.bedtime ? clock(form.sleep.bedtime, lang) : "–"],
                  [t("diary.stress"), form.stress === null ? "–" : n(form.stress)],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-2 border-b border-line pb-1.5">
                    <dt className="text-ink-soft">{k}</dt>
                    <dd className="font-semibold">{v}</dd>
                  </div>
                ))}
              </dl>
            </Card>
            {save.isError && <p className="mt-3 text-sm text-trigger">{t("app.error")}</p>}
          </div>
        )}
      </fieldset>

      <div className="mt-7 flex gap-3">
        {step > 0 && (
          <Button variant="outline" size="lg" onClick={() => setStep(step - 1)} aria-label={t("app.back")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
        )}
        {step < STEPS.length - 1 ? (
          <Button size="lg" className="flex-1" onClick={() => setStep(step + 1)}>
            {t("app.next")}
            <ArrowRight className="h-5 w-5" />
          </Button>
        ) : (
          <Button size="lg" className="flex-1" disabled={!editable || save.isPending} onClick={() => save.mutate(form)}>
            {save.isPending ? <LoaderCircle className="h-5 w-5 animate-spin" /> : <Check className="h-5 w-5" />}
            {t("diary.save")}
          </Button>
        )}
      </div>
    </div>
  );
}
