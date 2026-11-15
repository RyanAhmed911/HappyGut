import { useQuery } from "@tanstack/react-query";
import { ArrowRight, CalendarClock, Camera, ChevronRight, CircleCheck, Moon, Type } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { RiskCard, TrendChart } from "@/components/insights";
import { LoadError, SimulatedBadge, useLang, useProfile } from "@/components/shell";
import { Card, SectionTitle, Skeleton } from "@/components/ui";
import { VerdictDot } from "@/components/verdict";
import { api } from "@/lib/api";
import { dayOfTimestamp, longDate, num, shortDate, timeOfDay } from "@/lib/format";
import { keys, useToday } from "@/lib/hooks";

export function Today() {
  const { t } = useTranslation();
  const lang = useLang();
  const profile = useProfile();
  const today = useToday();
  const risk = useQuery({ queryKey: keys.risk, queryFn: api.risk });
  const periods = useQuery({ queryKey: keys.periods, queryFn: api.periods });
  const days = useQuery({ queryKey: keys.days(30), queryFn: () => api.days(30) });
  const diary = useQuery({ queryKey: keys.diary(today ?? ""), queryFn: () => api.diary(today!), enabled: !!today });
  const checks = useQuery({ queryKey: keys.mealChecks, queryFn: () => api.mealChecks(30) });

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "morning" : hour < 17 ? "afternoon" : "evening";
  const entry = diary.data?.entry;
  const upcoming = risk.data?.upcoming_periods[0];
  const recent = checks.data?.slice(0, 4) ?? [];
  const checkedToday = checks.data?.filter((c) => today && dayOfTimestamp(c.created_at) === today).length ?? 0;

  return (
    <div>
      <header className="mb-5 flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-ink-faint">{today ? longDate(today, lang) : " "}</p>
          <h1 className="mt-0.5 text-[28px] font-bold tracking-tight lg:text-[34px]">
            {t(`today.greeting_${greeting}`, { name: profile.data?.display_name ?? "" })}
          </h1>
          <p className="mt-1 text-[15px] text-ink-soft">
            {profile.data ? t(`today.state_${profile.data.state}`, { diagnosis: t(`today.dx_${profile.data.diagnosis}`) }) : " "}
          </p>
        </div>
        {profile.data?.is_synthetic && <SimulatedBadge className="hidden lg:inline-flex" />}
      </header>

      {upcoming && risk.data?.level !== "low" && (
        <Link to="/gut" className="mb-4 flex items-center gap-3 rounded-3xl bg-brand p-4 text-white shadow-float">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-white/15">
            <CalendarClock className="h-5 w-5" />
          </span>
          <span className="flex-1 text-sm leading-snug">
            <span className="block font-bold">{t("today.nudge_title", { name: upcoming.name, days: num(upcoming.days_until, lang) })}</span>
            <span className="text-white/85">{t("today.nudge_text")}</span>
          </span>
          <ChevronRight className="h-5 w-5 shrink-0 opacity-70" />
        </Link>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        <Link to="/check" className="group relative overflow-hidden rounded-3xl bg-ink p-5 text-white shadow-card transition active:scale-[0.99]">
          <div aria-hidden className="absolute -right-8 -top-8 h-28 w-28 rounded-full bg-brand/60" />
          <div className="relative">
            <div className="flex gap-2">
              <span className="grid h-10 w-10 place-items-center rounded-2xl bg-white/15">
                <Camera className="h-5 w-5" />
              </span>
              <span className="grid h-10 w-10 place-items-center rounded-2xl bg-white/15">
                <Type className="h-5 w-5" />
              </span>
            </div>
            <p className="mt-4 text-xl font-bold">{t("today.check_title")}</p>
            <p className="mt-0.5 text-sm text-white/75">{t("today.check_text")}</p>
            <p className="mt-3 inline-flex items-center gap-1 text-sm font-semibold text-saffron">
              {checkedToday ? t("today.checked_today", { n: num(checkedToday, lang) }) : t("today.check_cta")}
              <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
            </p>
          </div>
        </Link>

        <Link to="/diary" className="group rounded-3xl border border-line/70 bg-card p-5 shadow-card transition active:scale-[0.99]">
          <span className={`grid h-10 w-10 place-items-center rounded-2xl ${entry ? "bg-ok-soft text-ok" : "bg-brand-soft text-brand-deep"}`}>
            {entry ? <CircleCheck className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </span>
          <p className="mt-4 text-xl font-bold">{t("today.diary_title")}</p>
          {diary.isLoading ? (
            <div className="skeleton mt-2 h-5 w-40" />
          ) : entry ? (
            <p className="mt-0.5 text-sm text-ink-soft">
              {t("today.diary_done", { index: entry.index.name, score: num(entry.index.score, lang) })}
            </p>
          ) : (
            <p className="mt-0.5 text-sm text-ink-soft">{t("today.diary_text")}</p>
          )}
          <p className="mt-3 inline-flex items-center gap-1 text-sm font-semibold text-brand">
            {entry ? t("today.diary_edit") : t("today.diary_cta")}
            <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
          </p>
        </Link>
      </div>

      <SectionTitle>{t("today.outlook")}</SectionTitle>
      {risk.isLoading ? <Skeleton className="h-44" /> : risk.isError ? <LoadError onRetry={() => void risk.refetch()} /> : risk.data && <RiskCard risk={risk.data} compact />}

      <SectionTitle
        action={
          <Link to="/gut" className="text-sm font-semibold text-brand">
            {t("nav.gut")} →
          </Link>
        }
      >
        {t("today.last_30")}
      </SectionTitle>
      <Card className="p-4">
        {days.data && periods.data ? (
          days.data.days.length ? (
            <>
              <TrendChart days={days.data.days} periods={periods.data.periods} activeAt={periods.data.thresholds.active_at} height={170} />
              <p className="mt-1 px-1 text-xs text-ink-faint">{t("gut.chart_note", { index: periods.data.index_name, at: num(periods.data.thresholds.active_at, lang) })}</p>
            </>
          ) : (
            <p className="py-6 text-center text-sm text-ink-soft">{t("gut.no_days")}</p>
          )
        ) : (
          <Skeleton className="h-40" />
        )}
      </Card>

      <SectionTitle
        action={
          <Link to="/history" className="text-sm font-semibold text-brand">
            {t("app.see_all")} →
          </Link>
        }
      >
        {t("today.recent_checks")}
      </SectionTitle>
      {checks.isLoading ? (
        <Skeleton />
      ) : recent.length ? (
        <Card className="divide-y divide-line/70 p-0">
          {recent.map((c) => (
            <Link key={c.id} to={`/history/${c.id}`} className="flex items-center gap-3 px-4 py-3 first:rounded-t-3xl last:rounded-b-3xl hover:bg-paper/60">
              <VerdictDot verdict={c.verdict} />
              <span className="min-w-0 flex-1">
                <span className="block truncate font-semibold">{c.dishes.map((d) => d.name).join(", ")}</span>
                <span className="text-xs text-ink-faint">
                  {shortDate(dayOfTimestamp(c.created_at), lang)} · {timeOfDay(c.created_at, lang)} · {t(`verdict.${c.verdict}`)}
                </span>
              </span>
              <ChevronRight className="h-4 w-4 shrink-0 text-ink-faint" />
            </Link>
          ))}
        </Card>
      ) : (
        <Card className="text-sm text-ink-soft">{t("today.no_checks")}</Card>
      )}

      <p className="mt-8 text-center text-xs text-ink-faint">{t("app.disclaimer")}</p>
    </div>
  );
}
