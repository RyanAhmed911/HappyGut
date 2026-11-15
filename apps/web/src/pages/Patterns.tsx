import { useQuery } from "@tanstack/react-query";
import { Info, NotebookPen } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { PatternCard, RiskCard } from "@/components/insights";
import { LoadError, useLang } from "@/components/shell";
import { Button, Empty, PageTitle, SectionTitle, Sheet, Skeleton, Tabs } from "@/components/ui";
import { api } from "@/lib/api";
import { num } from "@/lib/format";
import { keys } from "@/lib/hooks";
import type { PatternLabel } from "@/lib/schemas";

const ORDER: PatternLabel[] = ["likely_contributor", "possible", "not_linked", "not_enough_data"];
type Scope = "all" | "remission" | "flare";

export function Patterns() {
  const { t } = useTranslation();
  const lang = useLang();
  const [scope, setScope] = useState<Scope>("all");
  const [how, setHow] = useState(false);
  const patterns = useQuery({ queryKey: keys.patterns(scope), queryFn: () => api.patterns(scope) });
  const risk = useQuery({ queryKey: keys.risk, queryFn: api.risk });
  const data = patterns.data;

  return (
    <div>
      <PageTitle
        title={t("patterns.title")}
        subtitle={t("patterns.subtitle")}
        action={
          <Button variant="ghost" size="icon" aria-label={t("patterns.how_title")} onClick={() => setHow(true)}>
            <Info className="h-5 w-5" />
          </Button>
        }
      />

      <Tabs
        value={scope}
        onChange={setScope}
        tabs={[
          { value: "all", label: t("patterns.scope_all") },
          { value: "remission", label: t("patterns.scope_remission") },
          { value: "flare", label: t("patterns.scope_flare") },
        ]}
      />

      <div className="mt-5">
        {patterns.isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-28" />
            <Skeleton className="h-28" />
            <Skeleton className="h-28" />
          </div>
        ) : patterns.isError || !data ? (
          <LoadError onRetry={() => void patterns.refetch()} />
        ) : !data.enough_data ? (
          <Empty icon={<NotebookPen className="h-8 w-8" />} title={t("patterns.need_more_title")}>
            <p>{t(scope === "all" ? "patterns.need_more" : "patterns.need_more_scope", { have: num(data.days_logged, lang), need: num(data.min_days, lang) })}</p>
            <Link to="/diary" className="mt-3 inline-block font-semibold text-brand">
              {t("today.diary_cta")} →
            </Link>
          </Empty>
        ) : (
          <>
            <p className="mb-1 text-sm text-ink-faint">{t("patterns.based_on", { days: num(data.days_logged, lang) })}</p>
            {ORDER.map((label) => {
              const items = data.results.filter((r) => r.label === label);
              if (!items.length) return null;
              return (
                <section key={label}>
                  <SectionTitle>
                    {t(`patterns.group_${label}`)} · {num(items.length, lang)}
                  </SectionTitle>
                  <div className="space-y-2.5">
                    {items.map((p) => (
                      <PatternCard key={p.factor} p={p} indexName={data.index_name} />
                    ))}
                  </div>
                </section>
              );
            })}
          </>
        )}
      </div>

      {scope === "all" && risk.data && (
        <>
          <SectionTitle>{t("today.outlook")}</SectionTitle>
          <RiskCard risk={risk.data} />
        </>
      )}

      <p className="mt-8 rounded-3xl bg-paper-deep/70 p-4 text-sm text-ink-soft">{t("patterns.footer")}</p>

      <Sheet open={how} onOpenChange={setHow} title={t("patterns.how_title")}>
        <ol className="space-y-3 text-[15px] text-ink-soft">
          {[1, 2, 3, 4].map((i) => (
            <li key={i} className="flex gap-3">
              <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-brand-soft text-sm font-bold text-brand-deep">{num(i, lang)}</span>
              <span>{t(`patterns.how_${i}`)}</span>
            </li>
          ))}
        </ol>
      </Sheet>
    </div>
  );
}
