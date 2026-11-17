import { useQuery } from "@tanstack/react-query";
import { BookOpen, Search, Sparkles, User } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { LoadError, PageLoading, useLang } from "@/components/shell";
import { Badge, Card, Chip, Empty, inputClass, PageTitle, Tabs } from "@/components/ui";
import { VerdictDot } from "@/components/verdict";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import { longDate, num } from "@/lib/format";
import type { GuideItem } from "@/lib/schemas";

const FILTERS = ["all", "likely_ok", "caution", "likely_trigger"] as const;
type Filter = (typeof FILTERS)[number];

function GuideRow({ item }: { item: GuideItem }) {
  const { t } = useTranslation();
  const lang = useLang();
  const name = lang === "bn" ? item.name_bn : item.name_en;
  const alt = item.alternative ? (lang === "bn" ? item.alternative.name_bn : item.alternative.name_en) : null;
  return (
    <li className="flex items-start gap-3 bg-card px-4 py-3">
      <VerdictDot verdict={item.verdict} className="mt-0.5" />
      <div className="min-w-0 flex-1">
        <p className="font-bold leading-snug">{name}</p>
        <p className="text-xs text-ink-faint">{lang === "bn" ? item.name_en : item.name_bn}</p>
        {item.components.length > 0 && (
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {item.components.map((c) => (
              <Badge key={c.component} tone={c.source === "personal" ? "saffron" : "neutral"}>
                {c.source === "personal" ? <User className="h-3 w-3" /> : <BookOpen className="h-3 w-3" />}
                {t(`component.${c.component}`)} · {t(`level.${c.level}`)}
              </Badge>
            ))}
          </div>
        )}
        {alt && (
          <p className="mt-1.5 flex items-center gap-1.5 text-sm text-ok">
            <Sparkles className="h-3.5 w-3.5" />
            {t("check.instead_try")} <span className="font-semibold">{alt}</span>
          </p>
        )}
      </div>
    </li>
  );
}

export function Foods() {
  const { t } = useTranslation();
  const lang = useLang();
  const [view, setView] = useState<"guide" | "plan">("guide");
  const [filter, setFilter] = useState<Filter>("all");
  const [q, setQ] = useState("");
  const guide = useQuery({ queryKey: ["foodGuide"], queryFn: api.foodGuide });
  const plan = useQuery({ queryKey: ["mealPlan"], queryFn: api.mealPlan, enabled: view === "plan" });

  const counts = useMemo(() => {
    const out: Record<string, number> = { all: guide.data?.length ?? 0 };
    for (const item of guide.data ?? []) out[item.verdict] = (out[item.verdict] ?? 0) + 1;
    return out;
  }, [guide.data]);
  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return (guide.data ?? []).filter(
      (i) => (filter === "all" || i.verdict === filter) && (!needle || i.name_en.toLowerCase().includes(needle) || i.name_bn.includes(needle)),
    );
  }, [guide.data, filter, q]);

  if (guide.isLoading) return <PageLoading />;
  if (guide.isError || !guide.data) return <LoadError onRetry={() => void guide.refetch()} />;

  return (
    <div>
      <PageTitle title={t("foods.title")} subtitle={t("foods.subtitle")} />
      <div className="lg:max-w-sm">
        <Tabs value={view} onChange={setView} tabs={[{ value: "guide", label: t("foods.tab_guide") }, { value: "plan", label: t("foods.tab_plan") }]} />
      </div>

      {view === "guide" ? (
        <div className="mt-4">
          <div className="lg:flex lg:items-center lg:gap-4">
          <div className="relative lg:w-80 lg:shrink-0">
            <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("foods.search")} className={cn(inputClass, "pl-10")} />
          </div>
          <div className="mt-3 flex flex-wrap gap-2 lg:mt-0">
            {FILTERS.map((f) => (
              <Chip key={f} selected={filter === f} className="min-h-9 text-[13px]" onClick={() => setFilter(f)}>
                {f === "all" ? t("foods.all") : t(`verdict.${f}`)} · {num(counts[f] ?? 0, lang)}
              </Chip>
            ))}
          </div>
          </div>
          {shown.length ? (
            <Card className="mt-4 overflow-hidden p-0">
              <ul className="grid gap-px bg-line md:grid-cols-2 xl:grid-cols-3">
                {shown.map((item) => (
                  <GuideRow key={item.dish_id} item={item} />
                ))}
              </ul>
            </Card>
          ) : (
            <div className="mt-4">
              <Empty title={t("foods.none")}>
                <Link to="/check" className="font-semibold text-brand">
                  {t("today.check_cta")} →
                </Link>
              </Empty>
            </div>
          )}
          <p className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-faint">
            <span className="inline-flex items-center gap-1">
              <BookOpen className="h-3 w-3" /> {t("check.evidence_guideline")}
            </span>
            <span className="inline-flex items-center gap-1">
              <User className="h-3 w-3" /> {t("check.evidence_personal")}
            </span>
          </p>
        </div>
      ) : plan.isLoading || !plan.data ? (
        <div className="mt-4 space-y-3">
          <div className="skeleton h-28" />
          <div className="skeleton h-28" />
        </div>
      ) : !plan.data.enough ? (
        <div className="mt-4">
          <Empty title={t("foods.plan_none")} />
        </div>
      ) : (
        <div className="mt-4">
          <p className="mb-3 text-sm text-ink-soft">{t("foods.plan_intro", { n: num(plan.data.pool_size, lang) })}</p>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {plan.data.days.map((day) => (
            <Card key={day.date} className="p-4">
              <p className="mb-2 text-[13px] font-bold uppercase tracking-[0.08em] text-ink-faint">{longDate(day.date, lang)}</p>
              <dl className="space-y-2">
                {(["breakfast", "lunch", "dinner"] as const).map((meal) => (
                  <div key={meal} className="flex gap-3">
                    <dt className="w-20 shrink-0 text-sm font-semibold text-ink-soft">{t(`foods.${meal}`)}</dt>
                    <dd className="flex flex-wrap gap-1.5">
                      {day.meals[meal].map((d) => (
                        <span key={d.dish_id} className="rounded-full bg-ok-soft px-2.5 py-1 text-sm font-medium text-ok">
                          {lang === "bn" ? d.name_bn : d.name_en}
                        </span>
                      ))}
                    </dd>
                  </div>
                ))}
              </dl>
            </Card>
          ))}
          </div>
        </div>
      )}

      <p className="mt-6 rounded-2xl bg-paper-deep/70 p-4 text-sm text-ink-soft">{t("foods.footer")}</p>
    </div>
  );
}
