import { useQuery } from "@tanstack/react-query";
import { Printer } from "lucide-react";
import { useTranslation } from "react-i18next";
import { TrendChart, useFactorName } from "@/components/insights";
import { LoadError, Logo, PageLoading, useLang } from "@/components/shell";
import { Button, PageTitle } from "@/components/ui";
import { api } from "@/lib/api";
import { dateRange, longDate, num, pct } from "@/lib/format";
import { keys } from "@/lib/hooks";
import type { DaySummary } from "@/lib/schemas";

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-line/70 py-1.5 text-sm">
      <dt className="text-ink-soft">{label}</dt>
      <dd className="text-right font-semibold">{value}</dd>
    </div>
  );
}

export function Report() {
  const { t } = useTranslation();
  const lang = useLang();
  const name = useFactorName();
  const report = useQuery({ queryKey: ["report"], queryFn: () => api.report(90) });
  const periods = useQuery({ queryKey: keys.periods, queryFn: api.periods });
  if (report.isLoading || periods.isLoading) return <PageLoading />;
  if (report.isError || !report.data || !periods.data) return <LoadError onRetry={() => void report.refetch()} />;
  const r = report.data;
  const n = (v: number | null, d = 0): string => (v === null ? "–" : num(v, lang, d));
  const days: DaySummary[] = r.series.map((s) => ({ date: s.date, index: s.index, stools: 0, pain: 0, sleep_hours: null, late_night: null, stress: null, medication: "na", period_kind: null, tags: [], food_reaction: false }));
  const adherence = r.adherence.logged ? r.adherence.taken / r.adherence.logged : null;
  const flares = r.periods.filter((p) => p.kind === "flare");
  const verdicts = ["likely_ok", "caution", "likely_trigger", "not_sure"] as const;

  return (
    <div>
      <div className="no-print">
        <PageTitle
          title={t("report.title")}
          subtitle={t("report.subtitle")}
          action={
            <Button onClick={() => window.print()}>
              <Printer className="h-4 w-4" />
              {t("report.print")}
            </Button>
          }
        />
      </div>

      <article className="rounded-3xl border border-line bg-card p-6 shadow-card print:border-0 print:p-0 print:shadow-none">
        <header className="flex flex-wrap items-start justify-between gap-3 border-b border-line pb-4">
          <div>
            <Logo />
            <h2 className="mt-3 text-2xl font-bold">{t("report.heading")}</h2>
            <p className="text-sm text-ink-soft">{dateRange(r.from, r.to, lang)}</p>
          </div>
          <div className="text-right text-sm">
            <p className="text-lg font-bold">{r.patient.display_name}</p>
            <p className="text-ink-soft">
              {t(`today.dx_${r.patient.diagnosis}`)} · {t(`gut.kind_${r.patient.current_state}`)}
            </p>
          </div>
        </header>

        <section className="mt-5 grid gap-x-8 gap-y-5 sm:grid-cols-2">
          <div>
            <h3 className="mb-1 text-[13px] font-bold uppercase tracking-[0.08em] text-ink-faint">{t("report.symptoms")}</h3>
            <dl>
              <Row label={t("report.days_logged")} value={`${n(r.days_logged)} / ${n(r.days_in_range)}`} />
              <Row label={t("gut.stat_avg", { index: r.index_name })} value={n(r.avg_index, 1)} />
              <Row label={t("report.worst")} value={n(r.worst_index)} />
              <Row label={t("gut.stat_blood")} value={n(r.days_with_blood)} />
              <Row label={t("report.flares")} value={n(flares.length)} />
            </dl>
          </div>
          <div>
            <h3 className="mb-1 text-[13px] font-bold uppercase tracking-[0.08em] text-ink-faint">{t("report.adherence")}</h3>
            <dl>
              <Row label={t("report.doses_taken")} value={adherence === null ? "–" : `${pct(adherence, lang)} (${n(r.adherence.taken)}/${n(r.adherence.logged)})`} />
              <Row label={t("report.doses_missed")} value={n(r.adherence.missed)} />
              <Row label={t("report.risk_now")} value={`${t(`risk.badge_${r.risk.level}`)} · ${n(r.risk.score)}/${n(100)}`} />
            </dl>
            <h3 className="mb-1 mt-4 text-[13px] font-bold uppercase tracking-[0.08em] text-ink-faint">{t("report.meals")}</h3>
            <dl>
              {verdicts.map((v) => (
                <Row key={v} label={t(`verdict.${v}`)} value={n(r.meal_verdicts[v] ?? 0)} />
              ))}
            </dl>
          </div>
        </section>

        <section className="mt-6">
          <h3 className="mb-2 text-[13px] font-bold uppercase tracking-[0.08em] text-ink-faint">{t("gut.trend", { index: r.index_name })}</h3>
          <TrendChart days={days} periods={periods.data.periods} activeAt={periods.data.thresholds.active_at} height={190} />
          {flares.length > 0 && (
            <p className="mt-2 text-sm text-ink-soft">
              {t("report.flare_list")}: {flares.map((p) => dateRange(p.start, p.end, lang)).join(" · ")}
            </p>
          )}
        </section>

        <section className="mt-6">
          <h3 className="mb-2 text-[13px] font-bold uppercase tracking-[0.08em] text-ink-faint">{t("report.contributors")}</h3>
          {r.contributors.length ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-left text-xs text-ink-faint">
                  <th className="py-1.5 font-semibold">{t("report.col_factor")}</th>
                  <th className="py-1.5 font-semibold">{t("report.col_label")}</th>
                  <th className="py-1.5 text-right font-semibold">{t("patterns.after_this")}</th>
                  <th className="py-1.5 text-right font-semibold">{t("patterns.other_days")}</th>
                </tr>
              </thead>
              <tbody>
                {r.contributors.map((c) => (
                  <tr key={c.factor} className="border-b border-line/60">
                    <td className="py-1.5 font-semibold">{name(c.factor)}</td>
                    <td className="py-1.5">{t(`patterns.label_${c.label}`)}</td>
                    <td className="tabular py-1.5 text-right">
                      {n(c.hits)}/{n(c.exposures)}
                    </td>
                    <td className="tabular py-1.5 text-right">
                      {n(c.baseline_hits)}/{n(c.baseline_days)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-sm text-ink-soft">{t("report.no_contributors")}</p>
          )}
          <p className="mt-2 text-xs text-ink-faint">{t("report.contributors_note")}</p>
        </section>

        <footer className="mt-6 border-t border-line pt-3 text-xs text-ink-faint">
          <p>{t("report.footer", { index: r.index_name })}</p>
          {r.is_synthetic && <p className="mt-1">{t("report.sample_data")}</p>}
          <p className="mt-1">
            {t("report.generated", { date: longDate(r.to, lang) })} · {t("app.disclaimer")}
          </p>
        </footer>
      </article>
    </div>
  );
}
