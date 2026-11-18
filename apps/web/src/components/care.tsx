import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarClock, Check, ChevronRight, Pill } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import { clock, daysBetween, num, shortDate } from "@/lib/format";
import { keys } from "@/lib/hooks";
import type { Appointment, Dose, Medications } from "@/lib/schemas";
import { useLang } from "./shell";

export function useMedications() {
  return useQuery({ queryKey: keys.medications, queryFn: api.medications });
}

export function useAppointments() {
  return useQuery({ queryKey: keys.appointments, queryFn: api.appointments });
}

/** "every day", "every week", "every 2 weeks" … */
export function useEvery(): (days: number) => string {
  const { t } = useTranslation();
  const lang = useLang();
  return (days) => (days === 1 ? t("care.every_day") : days === 7 ? t("care.every_week") : t("care.every_weeks", { n: num(days / 7, lang) }));
}

/** "today", "tomorrow", "in 5 days", or the date for anything further or past. */
export function useWhen(): (date: string, today: string) => string {
  const { t } = useTranslation();
  const lang = useLang();
  return (date, today) => {
    const d = daysBetween(today, date);
    if (d === 0) return t("care.when_today");
    if (d === 1) return t("care.when_tomorrow");
    if (d > 1 && d <= 30) return t("care.when_in_days", { n: num(d, lang) });
    return shortDate(date, lang);
  };
}

/** Today's scheduled doses with a tick for each. Ticking only records it; nothing is advised. */
export function DoseList({ data, compact }: { data: Medications; compact?: boolean }) {
  const { t } = useTranslation();
  const lang = useLang();
  const queryClient = useQueryClient();
  const mark = useMutation({
    mutationFn: (d: Dose) => api.markDose(data.day.date, d.medication_id, d.time, !d.taken),
    onSuccess: (fresh) => {
      queryClient.setQueryData(keys.medications, fresh);
      void queryClient.invalidateQueries({ queryKey: ["diary"] });
    },
  });
  if (!data.day.doses.length) return <p className="text-sm text-ink-soft">{t("care.no_doses_today")}</p>;
  return (
    <ul className={cn("divide-y divide-line", compact ? "" : "rounded-xl border border-line bg-card")}>
      {data.day.doses.map((d) => (
        <li key={`${d.medication_id}-${d.time}`} className={cn("flex items-center gap-3 py-2.5", compact ? "" : "px-3.5")}>
          <span className="tabular min-w-12 shrink-0 whitespace-nowrap text-sm font-semibold text-ink-soft">{clock(d.time, lang)}</span>
          <span className="min-w-0 flex-1">
            <span className={cn("block truncate font-semibold", d.taken && "text-ink-faint line-through decoration-ink-faint/40")}>{d.name}</span>
            {d.note && !compact && <span className="block truncate text-xs text-ink-faint">{d.note}</span>}
          </span>
          <button
            type="button"
            aria-pressed={d.taken}
            disabled={mark.isPending}
            onClick={() => mark.mutate(d)}
            className={cn(
              "inline-flex h-8 shrink-0 items-center gap-1.5 rounded-lg border px-2.5 text-xs font-semibold transition",
              d.taken ? "border-ok/30 bg-ok-soft text-ok" : "border-line bg-card text-ink-soft hover:border-brand/40",
            )}
          >
            <Check className="h-3.5 w-3.5" />
            {d.taken ? t("care.taken") : t("care.mark_taken")}
          </button>
        </li>
      ))}
    </ul>
  );
}

function NextAppointment({ a, today }: { a: Appointment; today: string }) {
  const { t } = useTranslation();
  const lang = useLang();
  const when = useWhen();
  return (
    <span className="flex items-center gap-2 text-sm">
      <CalendarClock className="h-4 w-4 shrink-0 text-brand" />
      <span>
        <span className="font-semibold">{t(`care.kind_${a.kind}`)}</span>
        <span className="text-ink-soft"> · {when(a.date, today)}{a.time ? ` · ${clock(a.time, lang)}` : ""}</span>
      </span>
    </span>
  );
}

/** On Today: today's doses and the next test within two weeks. Hidden when there is nothing to show. */
export function TodayCare() {
  const { t } = useTranslation();
  const meds = useMedications().data;
  const appts = useAppointments().data;
  const next = appts?.items.find((a) => a.date >= appts.today && daysBetween(appts.today, a.date) <= 14);
  if (!meds || (!meds.day.doses.length && !next)) return null;
  return (
    <div className="mt-3 rounded-2xl border border-line bg-card p-4 shadow-card">
      <div className="mb-1 flex items-center justify-between gap-3">
        <p className="flex items-center gap-2 font-bold">
          <Pill className="h-4 w-4 text-brand" />
          {t("care.today_title")}
        </p>
        <Link to="/care" className="inline-flex items-center text-sm font-semibold text-brand">
          {t("care.manage")}
          <ChevronRight className="h-4 w-4" />
        </Link>
      </div>
      {meds.day.doses.length > 0 && <DoseList data={meds} compact />}
      {next && appts && (
        <div className={cn(meds.day.doses.length > 0 && "mt-2 border-t border-line pt-3")}>
          <NextAppointment a={next} today={appts.today} />
        </div>
      )}
    </div>
  );
}
