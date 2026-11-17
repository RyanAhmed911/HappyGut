import {
  ArrowDown,
  BookOpen,
  Camera,
  CheckCircle2,
  Database,
  Eye,
  FileCheck2,
  FlaskConical,
  Gauge,
  Layers,
  Lock,
  MessageSquareText,
  Scale,
  ShieldCheck,
  Sparkles,
  Split,
} from "lucide-react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link, Outlet } from "react-router";
import { LangToggle, Logo, useLang } from "@/components/shell";
import { Card, PageTitle, SectionTitle } from "@/components/ui";
import evaluation from "@/data/evaluation.json";
import { auth } from "@/lib/api";
import { cn } from "@/lib/cn";
import { longDate, num, pct } from "@/lib/format";

/** Frame for people who are not signed in: the page is public so judges can read it first. */
export function PublicFrame() {
  const { t } = useTranslation();
  return (
    <div className="min-h-dvh">
      <header className="sticky top-0 z-20 border-b border-line bg-paper/85 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-3xl items-center justify-between gap-3 px-4 lg:h-16">
          <Link to="/welcome">
            <Logo className="[&>span]:text-lg" />
          </Link>
          <div className="flex items-center gap-2.5">
            <LangToggle />
            <Link to="/welcome" className="inline-flex h-9 items-center rounded-lg bg-brand px-3.5 text-sm font-semibold text-white shadow-float hover:bg-brand-deep">
              {t("about.sign_in")}
            </Link>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-3xl px-4 pb-16 pt-6 lg:pt-10">
        <Outlet />
      </main>
    </div>
  );
}

const STEPS = [
  { icon: Camera, tone: "plain" },
  { icon: Lock, tone: "guard" },
  { icon: Eye, tone: "ai" },
  { icon: Layers, tone: "plain" },
  { icon: Scale, tone: "engine" },
  { icon: MessageSquareText, tone: "ai" },
] as const;

const TONE = {
  plain: "bg-paper-deep text-ink-soft",
  guard: "bg-saffron-soft text-caution",
  ai: "bg-unsure-soft text-unsure",
  engine: "bg-brand text-white",
} as const;

function Stat({ value, label, note }: { value: string; label: string; note: string }) {
  return (
    <Card className="p-4">
      <p className="tabular text-2xl font-bold tracking-tight text-brand-deep">{value}</p>
      <p className="mt-1 text-sm font-semibold leading-snug">{label}</p>
      <p className="mt-1 text-xs text-ink-faint">{note}</p>
    </Card>
  );
}

function Item({ icon, title, children }: { icon: ReactNode; title: string; children: ReactNode }) {
  return (
    <div className="flex gap-3">
      <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-brand-soft text-brand-deep">{icon}</span>
      <div>
        <p className="font-bold leading-snug">{title}</p>
        <p className="mt-0.5 text-sm text-ink-soft">{children}</p>
      </div>
    </div>
  );
}

export function About() {
  const { t } = useTranslation();
  const lang = useLang();
  const n = (v: number): string => num(v, lang);
  const e = evaluation;
  const last = e.cohort.horizons[e.cohort.horizons.length - 1]!;

  return (
    <div>
      <PageTitle title={t("about.title")} subtitle={t("about.subtitle")} />

      {/* Input → AI → output */}
      <SectionTitle>{t("about.flow_title")}</SectionTitle>
      <ol className="space-y-2">
        {STEPS.map(({ icon: Icon, tone }, i) => (
          <li key={i}>
            <Card className={cn("flex gap-3.5 p-4", tone === "engine" && "border-brand/40 ring-1 ring-brand/15")}>
              <span className={cn("grid h-10 w-10 shrink-0 place-items-center rounded-lg", TONE[tone])}>
                <Icon className="h-5 w-5" />
              </span>
              <div className="min-w-0">
                <p className="font-bold leading-snug">
                  <span className="tabular mr-1.5 text-ink-faint">{n(i + 1)}</span>
                  {t(`about.step_${i + 1}_title`)}
                </p>
                <p className="mt-0.5 text-sm text-ink-soft">
                  {t(`about.step_${i + 1}_text`, { dishes: n(e.knowledge.dishes), rules: n(e.knowledge.rule_cards) })}
                </p>
              </div>
            </Card>
            <ArrowDown aria-hidden className="mx-auto mt-2 h-4 w-4 text-ink-faint" />
          </li>
        ))}
        <li>
          <div className="flex gap-3.5 rounded-2xl bg-brand-deep p-4 text-white">
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-white/15">
              <CheckCircle2 className="h-5 w-5" />
            </span>
            <div>
              <p className="font-bold leading-snug">{t("about.output_title")}</p>
              <p className="mt-0.5 text-sm text-white/80">{t("about.output_text")}</p>
            </div>
          </div>
        </li>
      </ol>

      <SectionTitle>{t("about.learn_title")}</SectionTitle>
      <Card className="space-y-4">
        <Item icon={<Sparkles className="h-[18px] w-[18px]" />} title={t("about.learn_patterns_title")}>
          {t("about.learn_patterns_text")}
        </Item>
        <Item icon={<Split className="h-[18px] w-[18px]" />} title={t("about.learn_periods_title")}>
          {t("about.learn_periods_text")}
        </Item>
        <Item icon={<Gauge className="h-[18px] w-[18px]" />} title={t("about.learn_risk_title")}>
          {t("about.learn_risk_text")}
        </Item>
      </Card>

      <SectionTitle>{t("about.safeguards_title")}</SectionTitle>
      <Card>
        <ul className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <li key={i} className="flex gap-2.5 text-sm">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
              <span>{t(`about.safe_${i}`)}</span>
            </li>
          ))}
        </ul>
      </Card>

      <SectionTitle>{t("about.results_title")}</SectionTitle>
      <p className="mb-3 text-sm text-ink-soft">{t("about.results_intro", { date: longDate(e.date, lang) })}</p>
      <div className="grid gap-3 sm:grid-cols-3">
        <Stat
          value={t("about.r_cohort_value", { found: n(last.found), of: n(last.of) })}
          label={t("about.r_cohort_label")}
          note={t("about.r_cohort_note", { patients: n(e.cohort.patients), days: n(e.cohort.days) })}
        />
        <Stat
          value={t("about.r_redflag_value", { caught: n(e.red_flags.caught), phrases: n(e.red_flags.phrases) })}
          label={t("about.r_redflag_label")}
          note={t("about.r_redflag_note", { false: n(e.red_flags.false_alarms), ordinary: n(e.red_flags.ordinary) })}
        />
        <Stat
          value={t("about.r_verdict_value", { identical: n(e.verdicts.identical), n: n(e.verdicts.assessments) })}
          label={t("about.r_verdict_label")}
          note={t("about.r_verdict_note", {
            dishes: n(e.verdicts.dishes),
            profiles: n(e.verdicts.profiles),
            rated: n(e.verdicts.stricture.rated),
            strict: n(e.verdicts.stricture.of),
          })}
        />
      </div>

      <Card className="mt-3 p-0">
        <p className="flex items-center gap-2 px-4 pt-4 font-bold">
          <FlaskConical className="h-4 w-4 text-brand" />
          {t("about.table_title")}
        </p>
        <div className="overflow-x-auto">
          <table className="mt-2 w-full text-sm">
            <thead>
              <tr className="border-y border-line bg-paper text-left text-xs font-bold uppercase tracking-[0.06em] text-ink-faint">
                <th className="px-4 py-2 font-bold">{t("about.table_days")}</th>
                <th className="px-4 py-2 font-bold">{t("about.table_found")}</th>
                <th className="w-2/5 px-4 py-2 font-bold">{t("about.table_share")}</th>
                <th className="px-4 py-2 text-right font-bold">{t("about.table_false")}</th>
              </tr>
            </thead>
            <tbody className="tabular">
              {e.cohort.horizons.map((h) => (
                <tr key={h.days} className="border-b border-line last:border-0">
                  <td className="px-4 py-2.5 font-semibold">{n(h.days)}</td>
                  <td className="px-4 py-2.5">
                    {n(h.found)} / {n(h.of)}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="flex items-center gap-2">
                      <span className="h-2 flex-1 overflow-hidden rounded-full bg-paper-deep">
                        <span className="block h-full rounded-full bg-brand" style={{ width: `${(100 * h.found) / h.of}%` }} />
                      </span>
                      <span className="w-10 text-right font-semibold">{pct(h.found / h.of, lang)}</span>
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-right">{n(h.false_reports)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="border-t border-line bg-saffron-soft/50 px-4 py-3 text-[13px] text-ink-soft">{t("about.simulated_note")}</p>
      </Card>
      <p className="mt-3 text-sm text-ink-soft">
        <span className="font-semibold text-ink">{t("about.not_yet_title")}:</span> {t("about.not_yet_text")}
      </p>

      <SectionTitle>{t("about.data_title")}</SectionTitle>
      <Card className="space-y-4">
        <Item icon={<BookOpen className="h-[18px] w-[18px]" />} title={t("about.data_1_title")}>
          {t("about.data_1_text")}
        </Item>
        <Item icon={<FileCheck2 className="h-[18px] w-[18px]" />} title={t("about.data_2_title")}>
          {t("about.data_2_text")}
        </Item>
        <Item icon={<Database className="h-[18px] w-[18px]" />} title={t("about.data_3_title")}>
          {t("about.data_3_text")}
        </Item>
        <Item icon={<Lock className="h-[18px] w-[18px]" />} title={t("about.data_4_title")}>
          {t("about.data_4_text")}
        </Item>
      </Card>

      <p className="mt-8 text-center text-xs text-ink-faint">{t("app.disclaimer")}</p>
      <p className="mt-4 text-center">
        <Link to={auth.token ? "/" : "/welcome"} className="text-sm font-semibold text-brand hover:underline">
          {auth.token ? t("about.back_app") : t("about.sign_in")} →
        </Link>
      </p>
    </div>
  );
}
