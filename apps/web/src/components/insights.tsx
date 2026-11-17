import { BedDouble, Brain, CalendarClock, ChevronDown, GraduationCap, Pill, TrendingUp, Utensils } from "lucide-react";
import { lazy, Suspense, useState } from "react";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/cn";
import { num } from "@/lib/format";
import { factorKey } from "@/lib/i18n";
import type { DaySummary, Pattern, PatternLabel, Risk, RiskDriver } from "@/lib/schemas";
import { useLang } from "./shell";
import type { TrendChartProps } from "./TrendChart";
import { Badge, type Tone } from "./ui";

// ---------------------------------------------------------------- factors

export function FactorIcon({ factor, className }: { factor: string; className?: string }) {
  const group = factor.split(":")[0];
  const Icon =
    group === "food" ? Utensils : group === "sleep" ? BedDouble : group === "stress" ? Brain : group === "medication" ? Pill : GraduationCap;
  return <Icon className={className} />;
}

export function useFactorName(): (factor: string) => string {
  const { t } = useTranslation();
  return (factor) => t(factorKey(factor));
}

// ---------------------------------------------------------------- flare risk

const RISK_COLOR = { low: "var(--color-ok)", raised: "var(--color-saffron)", high: "var(--color-trigger)" } as const;
const RISK_TONE: Record<Risk["level"], Tone> = { low: "ok", raised: "caution", high: "trigger" };

export function RiskGauge({ score, level }: { score: number; level: Risk["level"] }) {
  const lang = useLang();
  const r = 52;
  const half = Math.PI * r;
  return (
    <svg viewBox="0 0 128 76" className="w-36 shrink-0" role="img" aria-label={`${score}/100`}>
      <path d="M12 68 A52 52 0 0 1 116 68" fill="none" stroke="var(--color-paper-deep)" strokeWidth="12" strokeLinecap="round" />
      <path
        d="M12 68 A52 52 0 0 1 116 68"
        fill="none"
        stroke={RISK_COLOR[level]}
        strokeWidth="12"
        strokeLinecap="round"
        strokeDasharray={`${(Math.min(100, score) / 100) * half} ${half}`}
        style={{ transition: "stroke-dasharray 0.9s cubic-bezier(0.2,0.8,0.2,1)" }}
      />
      <text x="64" y="60" textAnchor="middle" className="fill-ink text-[26px] font-bold">
        {num(score, lang)}
      </text>
      <text x="64" y="74" textAnchor="middle" className="fill-ink-faint text-[9px] font-semibold">
        / {num(100, lang)}
      </text>
    </svg>
  );
}

export function useDriverText(risk: Risk): (d: RiskDriver) => string {
  const { t } = useTranslation();
  const lang = useLang();
  const name = useFactorName();
  return (d) => {
    switch (d.code) {
      case "index_trend":
        return t("risk.driver_trend", { value: num(d.value ?? 0, lang, 1) });
      case "factor":
        return t("risk.driver_factor", { factor: name(d.factor ?? ""), count: num(d.count ?? 0, lang), days: num(3, lang) });
      case "upcoming_period": {
        const type = (d.factor ?? "").split(":")[1];
        const p = risk.upcoming_periods.find((x) => x.type === type);
        return p ? t("risk.driver_upcoming", { name: p.name, days: num(p.days_until, lang) }) : name(d.factor ?? "");
      }
      case "missed_doses":
        return t("risk.driver_missed", { count: num(d.count ?? 0, lang) });
      case "in_flare":
        return t("risk.driver_in_flare");
    }
  };
}

export function RiskCard({ risk, compact }: { risk: Risk; compact?: boolean }) {
  const { t } = useTranslation();
  const lang = useLang();
  const text = useDriverText(risk);
  const drivers = risk.drivers.slice(0, compact ? 3 : 6);
  return (
    <div className="rounded-2xl border border-line bg-card p-5 shadow-card">
      <div className="flex items-center gap-4">
        <RiskGauge score={risk.score} level={risk.level} />
        <div className="min-w-0">
          <p className="text-[13px] font-bold uppercase tracking-[0.08em] text-ink-faint">{t("risk.title", { days: num(risk.horizon_days, lang) })}</p>
          <p className="mt-1 text-xl font-bold leading-snug">{risk.enough_data ? t(`risk.level_${risk.level}`) : t("risk.level_unknown")}</p>
          {risk.enough_data && (
            <Badge tone={RISK_TONE[risk.level]} className="mt-1.5">
              {t(`risk.badge_${risk.level}`)}
            </Badge>
          )}
        </div>
      </div>
      {!risk.enough_data ? (
        <p className="mt-4 text-sm text-ink-soft">{t("risk.not_enough")}</p>
      ) : drivers.length ? (
        <ul className="mt-4 space-y-2">
          <li className="text-xs font-semibold text-ink-faint">{t("risk.why")}</li>
          {drivers.map((d, i) => (
            <li key={i} className="flex items-center gap-2.5 text-sm">
              <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-paper-deep text-ink-soft">
                {d.code === "factor" ? (
                  <FactorIcon factor={d.factor ?? ""} className="h-3.5 w-3.5" />
                ) : d.code === "upcoming_period" ? (
                  <CalendarClock className="h-3.5 w-3.5" />
                ) : d.code === "missed_doses" ? (
                  <Pill className="h-3.5 w-3.5" />
                ) : (
                  <TrendingUp className="h-3.5 w-3.5" />
                )}
              </span>
              <span className="flex-1">{text(d)}</span>
              <span className="tabular text-xs font-bold text-ink-faint">+{num(d.points, lang)}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-4 text-sm text-ink-soft">{t("risk.calm")}</p>
      )}
      {risk.level !== "low" && <p className="mt-4 rounded-xl bg-paper px-3.5 py-2.5 text-xs text-ink-soft">{t("risk.advice")}</p>}
    </div>
  );
}

// ---------------------------------------------------------------- trend chart (the chart library loads on demand)

const LazyTrendChart = lazy(() => import("./TrendChart"));

export function TrendChart(props: TrendChartProps) {
  return (
    <Suspense fallback={<div className="skeleton" style={{ height: props.height ?? 220 }} />}>
      <LazyTrendChart {...props} />
    </Suspense>
  );
}

/** One small cell per day, coloured by period; a second row marks tagged stressful periods. */
export function PeriodStrip({ days }: { days: DaySummary[] }) {
  const { t } = useTranslation();
  if (!days.length) return null;
  const w = 100 / days.length;
  const color = (d: DaySummary): string =>
    d.period_kind === "flare" ? "var(--color-trigger)" : d.period_kind === "settling" ? "var(--color-saffron)" : d.period_kind === "remission" ? "var(--color-ok)" : "var(--color-line)";
  return (
    <div>
      <svg viewBox="0 0 100 9" preserveAspectRatio="none" className="h-7 w-full overflow-hidden rounded-lg" role="img" aria-label={t("gut.timeline")}>
        {days.map((d, i) => (
          <rect key={d.date} x={i * w} y={0} width={w + 0.05} height={6} fill={color(d)} opacity={d.period_kind === "flare" ? 0.95 : 0.55} />
        ))}
        {days.map((d, i) => (d.tags.length ? <rect key={`t${d.date}`} x={i * w} y={7} width={w + 0.05} height={2} fill="var(--color-brand)" /> : null))}
      </svg>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-soft">
        {(["remission", "flare", "settling"] as const).map((k) => (
          <span key={k} className="inline-flex items-center gap-1.5">
            <span className={cn("h-2.5 w-2.5 rounded-sm", k === "flare" ? "bg-trigger" : k === "settling" ? "bg-saffron" : "bg-ok/60")} />
            {t(`gut.kind_${k}`)}
          </span>
        ))}
        <span className="inline-flex items-center gap-1.5">
          <span className="h-1 w-3 rounded-sm bg-brand" />
          {t("gut.stressful_period")}
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- pattern cards

const LABEL_TONE: Record<PatternLabel, Tone> = { likely_contributor: "trigger", possible: "caution", not_linked: "ok", not_enough_data: "unsure" };

function RateBar({ rate, tone, label, value }: { rate: number; tone: string; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-[92px] shrink-0 text-ink-soft">{label}</span>
      <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-paper-deep">
        <div className={cn("h-full rounded-full", tone)} style={{ width: `${Math.round(Math.min(1, Math.max(0.02, rate)) * 100)}%` }} />
      </div>
      <span className="tabular w-14 shrink-0 text-right font-semibold">{value}</span>
    </div>
  );
}

export function PatternCard({ p, indexName }: { p: Pattern; indexName: string }) {
  const { t } = useTranslation();
  const lang = useLang();
  const name = useFactorName();
  const [open, setOpen] = useState(false);
  const n = (v: number, d = 0): string => num(v, lang, d);
  const enough = p.label !== "not_enough_data";
  return (
    <div className="rounded-2xl border border-line bg-card p-4 shadow-card">
      <button type="button" className="flex w-full items-start gap-3 text-left" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
        <span
          className={cn(
            "grid h-11 w-11 shrink-0 place-items-center rounded-xl",
            p.label === "likely_contributor" ? "bg-trigger-soft text-trigger" : p.label === "possible" ? "bg-caution-soft text-caution" : p.label === "not_linked" ? "bg-ok-soft text-ok" : "bg-unsure-soft text-unsure",
          )}
        >
          <FactorIcon factor={p.factor} className="h-5 w-5" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className="text-base font-bold leading-snug">{name(p.factor)}</span>
            <Badge tone={LABEL_TONE[p.label]}>{t(`patterns.label_${p.label}`)}</Badge>
          </span>
          <span className="mt-1 block text-sm text-ink-soft">
            {enough
              ? t("patterns.sentence", { hits: n(p.hits), n: n(p.exposures), bhits: n(p.baseline_hits), bn: n(p.baseline_days) })
              : t("patterns.not_enough", { n: n(p.exposures), need: n(3) })}
          </span>
          {enough && p.overlaps_with.length > 0 && (
            <span className="mt-1.5 inline-block rounded-lg bg-saffron-soft px-2 py-0.5 text-xs font-medium text-caution">
              {t("patterns.overlap_short", { list: p.overlaps_with.map(name).join(lang === "bn" ? " ও " : ", ") })}
            </span>
          )}
        </span>
        <ChevronDown className={cn("mt-1 h-4 w-4 shrink-0 text-ink-faint transition", open && "rotate-180")} />
      </button>

      {enough && (
        <div className="mt-3 space-y-1.5 pl-14">
          <RateBar rate={p.hits / Math.max(1, p.exposures)} tone={p.label === "likely_contributor" ? "bg-trigger" : p.label === "possible" ? "bg-saffron" : "bg-ok"} label={t("patterns.after_this")} value={`${n(p.hits)}/${n(p.exposures)}`} />
          <RateBar rate={p.baseline_hits / Math.max(1, p.baseline_days)} tone="bg-ink-faint/50" label={t("patterns.other_days")} value={`${n(p.baseline_hits)}/${n(p.baseline_days)}`} />
        </div>
      )}

      {open && (
        <dl className="mt-3 space-y-1.5 border-t border-line pt-3 pl-14 text-sm text-ink-soft">
          {p.avg_index_exposed !== null && p.avg_index_unexposed !== null && (
            <div>{t("patterns.avg_index", { index: indexName, a: n(p.avg_index_exposed, 1), b: n(p.avg_index_unexposed, 1) })}</div>
          )}
          <div>{t(`patterns.sure_${p.label}`)}</div>
          <div>{t(`patterns.window_${p.group}`)}</div>
          {p.overlaps_with.length > 0 && (
            <div className="rounded-lg bg-saffron-soft px-3 py-2 text-caution">
              {t("patterns.overlap", { list: p.overlaps_with.map(name).join(lang === "bn" ? " ও " : ", ") })}
            </div>
          )}
        </dl>
      )}
    </div>
  );
}
