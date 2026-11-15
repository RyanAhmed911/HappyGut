import { BookOpen, ChevronDown, CircleCheck, CircleHelp, FlaskConical, Phone, ShieldAlert, Sparkles, TriangleAlert, User } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/cn";
import { num } from "@/lib/format";
import type { Citation, DishVerdict, ExplanationEvent, RedFlag, VerdictCode, VerdictEvent } from "@/lib/schemas";
import { useLang } from "./shell";
import { Badge, Button, type Tone } from "./ui";

export const VERDICT_TONE: Record<VerdictCode, Tone> = {
  likely_ok: "ok",
  caution: "caution",
  likely_trigger: "trigger",
  not_sure: "unsure",
};

const ICON = { likely_ok: CircleCheck, caution: TriangleAlert, likely_trigger: ShieldAlert, not_sure: CircleHelp } as const;

const SURFACE: Record<VerdictCode, string> = {
  likely_ok: "bg-ok text-white",
  caution: "bg-saffron text-ink",
  likely_trigger: "bg-trigger text-white",
  not_sure: "bg-unsure text-white",
};
const SOFT: Record<VerdictCode, string> = {
  likely_ok: "bg-ok-soft text-ok border-ok/20",
  caution: "bg-caution-soft text-caution border-caution/20",
  likely_trigger: "bg-trigger-soft text-trigger border-trigger/20",
  not_sure: "bg-unsure-soft text-unsure border-unsure/20",
};

export function VerdictDot({ verdict, className }: { verdict: VerdictCode; className?: string }) {
  const Icon = ICON[verdict];
  return (
    <span className={cn("grid h-9 w-9 shrink-0 place-items-center rounded-full", SURFACE[verdict], className)}>
      <Icon className="h-5 w-5" strokeWidth={2.4} />
    </span>
  );
}

export function VerdictPill({ verdict }: { verdict: VerdictCode }) {
  const { t } = useTranslation();
  const Icon = ICON[verdict];
  return (
    <Badge tone={VERDICT_TONE[verdict]} className="py-1">
      <Icon className="h-3.5 w-3.5" />
      {t(`verdict.${verdict}`)}
    </Badge>
  );
}

/** The big verdict for the whole meal. */
export function VerdictHero({ verdict, confidence, note }: { verdict: VerdictCode; confidence: number; note?: string }) {
  const { t } = useTranslation();
  const lang = useLang();
  const Icon = ICON[verdict];
  return (
    <div className={cn("animate-pop relative overflow-hidden rounded-[28px] p-6", SURFACE[verdict])}>
      <div className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-white/10" />
      <div className="pointer-events-none absolute -bottom-14 right-10 h-32 w-32 rounded-full bg-white/10" />
      <div className="relative flex items-center gap-4">
        <span className="grid h-16 w-16 shrink-0 place-items-center rounded-full bg-white/20">
          <Icon className="h-9 w-9" strokeWidth={2.2} />
        </span>
        <div>
          <p className="text-sm font-semibold opacity-80">{t("check.verdict_for_meal")}</p>
          <p className="text-[26px] font-bold leading-tight">{t(`verdict.${verdict}`)}</p>
          <p className="mt-0.5 text-sm opacity-85">
            {t("check.confidence", { value: t(confidence >= 0.8 ? "check.conf_high" : confidence >= 0.5 ? "check.conf_medium" : "check.conf_low") })}
            {" · "}
            {num(Math.round(confidence * 100), lang)}%
          </p>
        </div>
      </div>
      {note && <p className="relative mt-4 rounded-xl bg-black/10 px-3 py-2 text-xs">{note}</p>}
    </div>
  );
}

function EvidenceBar({ dish }: { dish: DishVerdict }) {
  const { t } = useTranslation();
  const { guideline, personal } = dish.contributions;
  if (guideline <= 0 && personal <= 0) return null;
  const rows = [
    { key: "guideline", value: guideline, icon: BookOpen, color: "bg-brand" },
    { key: "personal", value: personal, icon: User, color: "bg-saffron" },
  ] as const;
  return (
    <div className="mt-4 space-y-2">
      {rows.map(({ key, value, icon: Icon, color }) => (
        <div key={key} className="flex items-center gap-2.5 text-xs">
          <Icon className="h-3.5 w-3.5 shrink-0 text-ink-faint" />
          <span className="w-28 shrink-0 text-ink-soft">{t(`check.evidence_${key}`)}</span>
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-paper-deep">
            <div className={cn("h-full rounded-full transition-all duration-700", color)} style={{ width: `${Math.round(Math.min(1, value) * 100)}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function CitationRow({ c }: { c: Citation }) {
  const { t } = useTranslation();
  const lang = useLang();
  if (c.type === "guideline") {
    return (
      <li className="rounded-2xl bg-brand-tint p-3">
        <p className="flex items-center gap-1.5 text-xs font-bold text-brand-deep">
          <BookOpen className="h-3.5 w-3.5" />
          {t("check.cite_guideline")}
          {c.strict_rule && <Badge tone="trigger">{t("check.strict_rule")}</Badge>}
        </p>
        <p className="mt-1 text-sm font-semibold">{c.title}</p>
        <p className="text-sm text-ink-soft">{c.recommendation}</p>
        {c.sources?.map((s) => (
          <p key={s} className="mt-1.5 text-xs italic text-ink-faint">
            {s}
          </p>
        ))}
        <p className="mt-1 font-mono text-[10px] text-ink-faint">{c.id}</p>
      </li>
    );
  }
  if (c.type === "personal") {
    const key = c.tolerated ? "check.personal_tolerated" : (c.probability ?? 0) > 0.8 ? "check.personal_linked" : "check.personal_unclear";
    return (
      <li className="rounded-2xl bg-saffron-soft p-3">
        <p className="flex items-center gap-1.5 text-xs font-bold text-caution">
          <User className="h-3.5 w-3.5" />
          {t("check.cite_personal")}
        </p>
        <p className="mt-1 text-sm">
          {t(key, { component: t(`component.${c.component}`), n: num(c.exposures ?? 0, lang) })}
        </p>
      </li>
    );
  }
  return (
    <li className="rounded-2xl bg-paper p-3">
      <p className="flex items-center gap-1.5 text-xs font-bold text-ink-soft">
        <FlaskConical className="h-3.5 w-3.5" />
        {t("check.cite_composition")}
      </p>
      <div className="mt-1.5 flex flex-wrap gap-1.5">
        {c.components?.length ? (
          c.components.map((x) => (
            <Badge key={x.component} tone={x.level === "high" ? "trigger" : "caution"}>
              {t(`component.${x.component}`)} · {t(`level.${x.level}`)}
            </Badge>
          ))
        ) : (
          <span className="text-sm text-ink-soft">{t("check.no_notable_components")}</span>
        )}
      </div>
    </li>
  );
}

export function DishCard({ dish, explanation }: { dish: DishVerdict; explanation?: ExplanationEvent["dishes"][number] }) {
  const { t } = useTranslation();
  const lang = useLang();
  const [open, setOpen] = useState(false);
  const citations = explanation?.citations ?? [];
  return (
    <div className={cn("animate-rise rounded-3xl border bg-card p-5 shadow-card", SOFT[dish.verdict].split(" ").at(-1))}>
      <div className="flex items-start gap-3">
        <VerdictDot verdict={dish.verdict} />
        <div className="min-w-0 flex-1">
          <h3 className="text-lg font-bold leading-snug">{dish.name}</h3>
          <p className={cn("text-sm font-semibold", SOFT[dish.verdict].split(" ")[1])}>{t(`verdict.${dish.verdict}`)}</p>
        </div>
      </div>

      {explanation ? <p className="mt-3 text-[15px] text-ink-soft">{explanation.text}</p> : <div className="skeleton mt-3 h-12" />}

      <EvidenceBar dish={dish} />

      {dish.alternative?.name && (
        <div className="mt-4 flex items-center gap-2.5 rounded-2xl bg-ok-soft px-3.5 py-2.5 text-sm">
          <Sparkles className="h-4 w-4 shrink-0 text-ok" />
          <span>
            <span className="text-ink-soft">{t("check.instead_try")} </span>
            <span className="font-bold text-ok">{dish.alternative.name}</span>
          </span>
        </div>
      )}

      {citations.length > 0 && (
        <div className="mt-3">
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            className="flex w-full items-center justify-between rounded-xl py-1.5 text-sm font-semibold text-brand"
          >
            {t("check.why_evidence", { n: num(citations.length, lang) })}
            <ChevronDown className={cn("h-4 w-4 transition", open && "rotate-180")} />
          </button>
          {open && <ul className="mt-2 space-y-2">{citations.map((c) => <CitationRow key={c.id} c={c} />)}</ul>}
        </div>
      )}
    </div>
  );
}

export function MealResult({ verdict, explanation }: { verdict: VerdictEvent; explanation?: ExplanationEvent }) {
  const { t } = useTranslation();
  const question = verdict.clarifying_question ?? explanation?.clarifying_question;
  return (
    <div className="space-y-3">
      <VerdictHero verdict={verdict.verdict} confidence={verdict.confidence} note={verdict.note} />
      {question && (
        <div className="animate-rise flex gap-3 rounded-3xl border border-unsure/20 bg-unsure-soft p-4 text-[15px]">
          <CircleHelp className="mt-0.5 h-5 w-5 shrink-0 text-unsure" />
          <div>
            <p className="font-semibold">{t("check.we_need_to_know")}</p>
            <p className="text-ink-soft">{question}</p>
          </div>
        </div>
      )}
      {verdict.dishes.map((dish, i) => (
        <DishCard key={`${dish.name}-${i}`} dish={dish} explanation={explanation?.dishes[i]} />
      ))}
      <p className="px-2 text-center text-xs text-ink-faint">{t("check.engine_note", { version: verdict.engine_version })}</p>
    </div>
  );
}

/** Red-flag escalation: no diet advice, only "get medical help" (Constitution II). */
export function Escalation({ flag, onClose }: { flag: RedFlag; onClose?: () => void }) {
  const { t } = useTranslation();
  return (
    <div role="alertdialog" aria-labelledby="escalation-title" className="animate-pop overflow-hidden rounded-[28px] bg-trigger text-white shadow-2xl">
      <div className="p-6">
        <span className="grid h-14 w-14 place-items-center rounded-full bg-white/20">
          <ShieldAlert className="h-8 w-8" />
        </span>
        <h2 id="escalation-title" className="mt-4 text-2xl font-bold">
          {flag.title}
        </h2>
        <p className="mt-2 text-[15px] leading-relaxed text-white/90">{flag.message}</p>
        {flag.reasons.length > 0 && (
          <ul className="mt-4 space-y-1.5 rounded-2xl bg-black/15 p-4 text-sm">
            <li className="text-xs font-bold uppercase tracking-wide text-white/70">{t("redflag.because")}</li>
            {flag.reasons.map((r) => (
              <li key={r} className="flex gap-2">
                <span aria-hidden>•</span>
                {r}
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="space-y-2.5 bg-black/15 p-5">
        <a href="tel:999" className="flex h-14 items-center justify-center gap-2 rounded-2xl bg-white text-base font-bold text-trigger active:scale-[0.98]">
          <Phone className="h-5 w-5" />
          {t("redflag.call_999")}
        </a>
        <p className="text-center text-xs text-white/80">{t("redflag.no_advice")}</p>
        {onClose && (
          <Button variant="ghost" className="w-full text-white hover:bg-white/10" onClick={onClose}>
            {t("redflag.understood")}
          </Button>
        )}
      </div>
    </div>
  );
}
