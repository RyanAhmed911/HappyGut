import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Camera, ChevronRight, ScanLine, Type } from "lucide-react";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";
import { LoadError, PageLoading, useLang } from "@/components/shell";
import { Card, Empty, PageTitle } from "@/components/ui";
import { MealResult, VerdictDot } from "@/components/verdict";
import { api } from "@/lib/api";
import { dayOfTimestamp, longDate, timeOfDay } from "@/lib/format";
import { keys, useDishName } from "@/lib/hooks";
import type { MealCheck } from "@/lib/schemas";

export function History() {
  const { t } = useTranslation();
  const lang = useLang();
  const dishName = useDishName(lang);
  const checks = useQuery({ queryKey: keys.mealChecks, queryFn: () => api.mealChecks(30) });
  const groups = useMemo(() => {
    const map = new Map<string, MealCheck[]>();
    for (const c of checks.data ?? []) {
      const day = dayOfTimestamp(c.created_at);
      map.set(day, [...(map.get(day) ?? []), c]);
    }
    return [...map.entries()];
  }, [checks.data]);

  if (checks.isLoading) return <PageLoading />;
  if (checks.isError) return <LoadError onRetry={() => void checks.refetch()} />;
  return (
    <div>
      <PageTitle title={t("history.title")} subtitle={t("history.subtitle")} />
      {groups.length === 0 ? (
        <Empty icon={<ScanLine className="h-8 w-8" />} title={t("today.no_checks")}>
          <Link to="/check" className="font-semibold text-brand">
            {t("today.check_cta")} →
          </Link>
        </Empty>
      ) : (
        groups.map(([day, items]) => (
          <section key={day} className="mb-5">
            <h2 className="mb-2 text-[13px] font-bold uppercase tracking-[0.08em] text-ink-faint">{longDate(day, lang)}</h2>
            <Card className="divide-y divide-line/70 p-0">
              {items.map((c) => (
                <Link key={c.id} to={`/history/${c.id}`} className="flex items-center gap-3 px-4 py-3 hover:bg-paper/60">
                  <VerdictDot verdict={c.verdict} />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-semibold">{c.dishes.map(dishName).join(", ")}</span>
                    <span className="flex items-center gap-1.5 text-xs text-ink-faint">
                      {c.input_type === "photo" ? <Camera className="h-3 w-3" /> : <Type className="h-3 w-3" />}
                      {timeOfDay(c.created_at, lang)} · {t(`verdict.${c.verdict}`)}
                    </span>
                  </span>
                  <ChevronRight className="h-4 w-4 shrink-0 text-ink-faint" />
                </Link>
              ))}
            </Card>
          </section>
        ))
      )}
    </div>
  );
}

export function HistoryDetail() {
  const { t } = useTranslation();
  const lang = useLang();
  const { id = "" } = useParams();
  const check = useQuery({ queryKey: ["mealCheck", id], queryFn: () => api.mealCheckById(id) });
  if (check.isLoading) return <PageLoading />;
  if (check.isError || !check.data) return <LoadError onRetry={() => void check.refetch()} />;
  const c = check.data;
  return (
    <div>
      <Link to="/history" className="mb-3 inline-flex items-center gap-1.5 text-sm font-semibold text-brand">
        <ArrowLeft className="h-4 w-4" />
        {t("history.title")}
      </Link>
      <PageTitle title={t("check.result_title")} subtitle={`${longDate(dayOfTimestamp(c.created_at), lang)} · ${timeOfDay(c.created_at, lang)}`} />
      <MealResult
        verdict={{ verdict: c.verdict, risk: c.risk, confidence: c.confidence, engine_version: c.engine_version, dishes: c.dishes, clarifying_question: c.explanation.clarifying_question }}
        explanation={c.explanation}
      />
    </div>
  );
}
