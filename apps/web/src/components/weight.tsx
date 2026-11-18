import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronRight, Plus, Scale, Trash2, TriangleAlert } from "lucide-react";
import { lazy, Suspense, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import { num, shortDate } from "@/lib/format";
import { keys, PERSONAL_KEYS } from "@/lib/hooks";
import type { Weight, WeightLoss } from "@/lib/schemas";
import { useLang } from "./shell";
import { Button, Card, Field, inputClass, Sheet } from "./ui";

const LazyWeightChart = lazy(() => import("./WeightChart"));
/** Colour a change as a drop only when it is more than everyday scale noise. */
const NOTABLE_DROP_PERCENT = 2;

export function useWeights() {
  return useQuery({ queryKey: keys.weights, queryFn: api.weights });
}

/** "−3.4 kg" / "+0.6 kg", with the language's digits. */
export function signedKg(kg: number, lang: string): string {
  const sign = kg > 0 ? "+" : kg < 0 ? "−" : "±";
  return `${sign}${num(Math.abs(kg), lang, 1)}`;
}

/** The weight-loss notice: a warning sign to tell the doctor about, never a diagnosis. */
export function WeightNotice({ loss, w, compact }: { loss: WeightLoss; w: Weight; compact?: boolean }) {
  const { t } = useTranslation();
  const lang = useLang();
  const vars = {
    percent: num(loss.percent, lang, 1),
    kg: num(loss.kg, lang, 1),
    date: shortDate(loss.peak.date, lang),
    threshold: num(loss.window === "recent" ? w.thresholds.recent_percent : w.thresholds.long_percent, lang),
  };
  return (
    <div role="status" className="flex gap-3 rounded-xl border border-caution/25 bg-caution-soft p-3.5 text-sm">
      <TriangleAlert className="mt-0.5 h-5 w-5 shrink-0 text-caution" />
      <div>
        <p className="font-bold text-ink">{t("weight.loss_title", vars)}</p>
        {!compact && (
          <>
            <p className="mt-1 text-ink-soft">{t(`weight.loss_text_${loss.window}`, vars)}</p>
            <p className="mt-1 font-semibold text-ink">{t(loss.level === "larger" ? "weight.loss_action_larger" : "weight.loss_action")}</p>
            <p className="mt-1.5 text-xs text-ink-faint">{t("weight.source", { citation: w.source.citation, pmid: w.source.pmid })}</p>
          </>
        )}
      </div>
    </div>
  );
}

function AddWeight({ open, onOpenChange, w }: { open: boolean; onOpenChange: (o: boolean) => void; w: Weight }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [day, setDay] = useState(w.today);
  const [kg, setKg] = useState(w.latest ? String(w.latest.kg) : "");
  const value = Number(kg.replace(",", "."));
  const valid = kg.trim() !== "" && Number.isFinite(value) && value >= w.thresholds.min_kg && value <= w.thresholds.max_kg;
  const save = useMutation({
    mutationFn: () => api.saveWeight(day, value),
    onSuccess: (fresh) => {
      queryClient.setQueryData(keys.weights, fresh);
      for (const key of PERSONAL_KEYS) void queryClient.invalidateQueries({ queryKey: [...key] });
      onOpenChange(false);
    },
  });
  return (
    <Sheet open={open} onOpenChange={onOpenChange} title={t("weight.add")} description={t("weight.add_hint")}>
      <div className="grid grid-cols-2 gap-3">
        <Field label={t("weight.weight_label")}>
          <input
            inputMode="decimal"
            className={inputClass}
            value={kg}
            onChange={(e) => setKg(e.target.value)}
            placeholder="55.0"
            aria-describedby="weight-unit"
          />
          <span id="weight-unit" className="mt-1 block text-xs text-ink-faint">{t("weight.unit")}</span>
        </Field>
        <Field label={t("weight.date_label")}>
          <input type="date" className={inputClass} value={day} max={w.today} onChange={(e) => setDay(e.target.value)} />
        </Field>
      </div>
      {save.isError && <p className="mb-3 text-sm text-trigger">{t("weight.save_error")}</p>}
      <Button className="w-full" disabled={!valid || !day || save.isPending} onClick={() => save.mutate()}>
        {t("app.save")}
      </Button>
    </Sheet>
  );
}

/** The weight section on My Gut: trend, changes, the notice, adding and removing weigh-ins. */
export function WeightSection() {
  const { t } = useTranslation();
  const lang = useLang();
  const queryClient = useQueryClient();
  const weights = useWeights();
  const [adding, setAdding] = useState(false);
  const remove = useMutation({
    mutationFn: (day: string) => api.deleteWeight(day),
    onSuccess: () => {
      for (const key of PERSONAL_KEYS) void queryClient.invalidateQueries({ queryKey: [...key] });
    },
  });
  const w = weights.data;
  if (weights.isLoading) return <div className="skeleton h-48" />;
  if (!w) return null;
  const recent = [...w.entries].reverse().slice(0, 4);

  return (
    <Card id="weight" className="scroll-mt-24 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="font-bold">{t("weight.title")}</h2>
          <p className="text-xs text-ink-faint">{t("weight.subtitle")}</p>
        </div>
        <Button size="sm" variant={w.due ? "primary" : "outline"} className="shrink-0 whitespace-nowrap" onClick={() => setAdding(true)}>
          <Plus className="h-4 w-4" />
          {t("weight.add_short")}
        </Button>
      </div>

      {w.latest ? (
        <>
          <div className="mt-3 flex flex-wrap items-end gap-x-5 gap-y-2">
            <div>
              <p className="tabular text-3xl font-bold tracking-tight">{num(w.latest.kg, lang, 1)}<span className="ml-1 text-base font-semibold text-ink-faint">{t("weight.unit_short")}</span></p>
              <p className="text-xs text-ink-faint">{t("weight.latest_on", { date: shortDate(w.latest.date, lang) })}</p>
            </div>
            {w.changes.map((c) => (
              <div key={c.days}>
                <p className={cn("tabular text-sm font-bold", c.percent <= -NOTABLE_DROP_PERCENT ? "text-caution" : "text-ink")}>{signedKg(c.kg, lang)} {t("weight.unit_short")}</p>
                <p className="text-xs text-ink-faint">{t("weight.in_days", { n: num(c.days, lang) })}</p>
              </div>
            ))}
          </div>
          {w.entries.length >= 2 && (
            <div className="mt-3">
              <Suspense fallback={<div className="skeleton h-40" />}>
                <LazyWeightChart entries={w.entries} peak={w.loss?.peak} />
              </Suspense>
            </div>
          )}
          {w.loss && (
            <div className="mt-3">
              <WeightNotice loss={w.loss} w={w} />
            </div>
          )}
          {w.due && <p className="mt-3 text-sm text-ink-soft">{t("weight.due")}</p>}
          <ul className="mt-3 divide-y divide-line border-t border-line text-sm">
            {recent.map((e) => (
              <li key={e.date} className="flex items-center justify-between gap-3 py-2">
                <span className="text-ink-soft">{shortDate(e.date, lang)}</span>
                <span className="flex items-center gap-2">
                  <span className="tabular font-semibold">{t("weight.kg", { value: num(e.kg, lang, 1) })}</span>
                  <button
                    type="button"
                    aria-label={t("app.remove")}
                    disabled={remove.isPending}
                    onClick={() => remove.mutate(e.date)}
                    className="rounded-lg p-1.5 text-ink-faint hover:bg-paper-deep hover:text-trigger"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </span>
              </li>
            ))}
          </ul>
        </>
      ) : (
        <div className="mt-3 rounded-xl border border-dashed border-line px-4 py-6 text-center">
          <Scale className="mx-auto h-7 w-7 text-ink-faint" />
          <p className="mt-2 font-semibold">{t("weight.empty_title")}</p>
          <p className="mt-1 text-sm text-ink-soft">{t("weight.empty_text")}</p>
        </div>
      )}
      <p className="mt-3 text-xs text-ink-faint">{t("weight.why", { percent: num(w.thresholds.recent_percent, lang) })}</p>
      <AddWeight key={`${w.today}-${w.latest?.kg ?? ""}`} open={adding} onOpenChange={setAdding} w={w} />
    </Card>
  );
}

/** On Today: the notice when weight has dropped past the threshold, else a reminder when a weigh-in is due. */
export function TodayWeight() {
  const { t } = useTranslation();
  const w = useWeights().data;
  if (!w || (!w.loss && !w.due)) return null;
  return (
    <Link to="/gut#weight" className="group mt-3 block">
      {w.loss ? (
        <div className="relative">
          <WeightNotice loss={w.loss} w={w} compact />
          <ChevronRight className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
        </div>
      ) : (
        <div className="flex items-center gap-3 rounded-xl border border-line bg-card p-3.5 text-sm shadow-card transition group-hover:border-brand/40">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-brand-soft text-brand-deep">
            <Scale className="h-[18px] w-[18px]" />
          </span>
          <span className="flex-1">
            <span className="block font-semibold">{t("weight.today_title")}</span>
            <span className="text-ink-soft">{t("weight.today_text")}</span>
          </span>
          <ChevronRight className="h-4 w-4 text-ink-faint" />
        </div>
      )}
    </Link>
  );
}
