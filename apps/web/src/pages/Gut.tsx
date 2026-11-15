import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarPlus, Flame, GraduationCap, Leaf, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router";
import { FactorIcon, PeriodStrip, TrendChart, useFactorName } from "@/components/insights";
import { LoadError, PageLoading, useLang } from "@/components/shell";
import { Badge, Button, Card, Chip, Empty, Field, inputClass, PageTitle, SectionTitle, Sheet, Tabs } from "@/components/ui";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import { dateRange, daysBetween, num, shortDate } from "@/lib/format";
import { keys, PERSONAL_KEYS, useToday } from "@/lib/hooks";
import { PERIOD_TYPES, type Period, type PeriodSummary, type StressPeriod } from "@/lib/schemas";

function useRefreshPersonal(): () => void {
  const queryClient = useQueryClient();
  return () => {
    for (const key of [...PERSONAL_KEYS, ["stressPeriods"]]) void queryClient.invalidateQueries({ queryKey: [...key] });
  };
}

function StatTile({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-2xl border border-line/70 bg-card p-3.5 shadow-card">
      <p className="text-xs font-semibold text-ink-faint">{label}</p>
      <p className="tabular mt-0.5 text-2xl font-bold">{value}</p>
      {sub && <p className="text-xs text-ink-faint">{sub}</p>}
    </div>
  );
}

function SummaryTiles({ s, indexName }: { s: PeriodSummary; indexName: string }) {
  const { t } = useTranslation();
  const lang = useLang();
  const n = (v: number | null | undefined, d = 0): string => (v === null || v === undefined ? "–" : num(v, lang, d));
  if (!s.days) return <Empty title={t("gut.no_days_of_kind")} />;
  return (
    <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
      <StatTile label={t("gut.stat_days")} value={n(s.days)} sub={t("gut.stat_periods", { n: n(s.periods) })} />
      <StatTile label={t("gut.stat_avg", { index: indexName })} value={n(s.avg_index, 1)} sub={t("gut.stat_worst", { n: n(s.worst_index) })} />
      <StatTile label={t("gut.stat_stools")} value={n(s.avg_stools, 1)} />
      <StatTile label={t("gut.stat_blood")} value={n(s.days_with_blood)} />
      <StatTile label={t("gut.stat_pain")} value={n(s.avg_pain, 1)} sub={t("gut.stat_pain_scale")} />
      <StatTile label={t("gut.stat_sleep")} value={n(s.avg_sleep_hours, 1)} sub={t("gut.stat_late", { n: n(s.late_nights) })} />
    </div>
  );
}

function AddStressPeriod({ open, onOpenChange, today }: { open: boolean; onOpenChange: (o: boolean) => void; today: string }) {
  const { t } = useTranslation();
  const refresh = useRefreshPersonal();
  const [type, setType] = useState<StressPeriod["type"]>("exam");
  const [name, setName] = useState("");
  const [start, setStart] = useState(today);
  const [end, setEnd] = useState(today);
  const add = useMutation({
    mutationFn: () => api.addStressPeriod({ type, name: name.trim() || t(`periodType.${type}`), start, end }),
    onSuccess: () => {
      refresh();
      onOpenChange(false);
      setName("");
    },
  });
  return (
    <Sheet open={open} onOpenChange={onOpenChange} title={t("gut.add_period")} description={t("gut.add_period_hint")}>
      <Field label={t("gut.period_type")}>
        <div className="flex flex-wrap gap-1.5">
          {PERIOD_TYPES.map((x) => (
            <Chip key={x} selected={type === x} className="min-h-9 text-[13px]" onClick={() => setType(x)}>
              {t(`periodType.${x}`)}
            </Chip>
          ))}
        </div>
      </Field>
      <Field label={t("gut.period_name")}>
        <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} maxLength={60} placeholder={t("gut.period_name_ph")} />
      </Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label={t("gut.from")}>
          <input type="date" className={inputClass} value={start} onChange={(e) => { setStart(e.target.value); if (e.target.value > end) setEnd(e.target.value); }} />
        </Field>
        <Field label={t("gut.to")}>
          <input type="date" className={inputClass} value={end} min={start} onChange={(e) => setEnd(e.target.value)} />
        </Field>
      </div>
      {add.isError && <p className="mb-3 text-sm text-trigger">{t("gut.bad_range")}</p>}
      <Button className="w-full" disabled={add.isPending || !start || !end || end < start} onClick={() => add.mutate()}>
        {t("app.save")}
      </Button>
    </Sheet>
  );
}

function MarkFlare({ open, onOpenChange, today }: { open: boolean; onOpenChange: (o: boolean) => void; today: string }) {
  const { t } = useTranslation();
  const refresh = useRefreshPersonal();
  const [start, setStart] = useState(today);
  const [end, setEnd] = useState("");
  const add = useMutation({
    mutationFn: () => api.addFlare(start, end || null),
    onSuccess: () => {
      refresh();
      onOpenChange(false);
    },
  });
  return (
    <Sheet open={open} onOpenChange={onOpenChange} title={t("gut.mark_flare")} description={t("gut.mark_flare_hint")}>
      <div className="grid grid-cols-2 gap-3">
        <Field label={t("gut.from")}>
          <input type="date" className={inputClass} value={start} max={today} onChange={(e) => setStart(e.target.value)} />
        </Field>
        <Field label={t("gut.to")} hint={t("gut.still_going")}>
          <input type="date" className={inputClass} value={end} min={start} max={today} onChange={(e) => setEnd(e.target.value)} />
        </Field>
      </div>
      {add.isError && <p className="mb-3 text-sm text-trigger">{t("gut.bad_range")}</p>}
      <Button className="w-full" disabled={add.isPending || !start} onClick={() => add.mutate()}>
        {t("app.save")}
      </Button>
    </Sheet>
  );
}

export function Gut() {
  const { t } = useTranslation();
  const lang = useLang();
  const today = useToday();
  const refresh = useRefreshPersonal();
  const name = useFactorName();
  const { hash } = useLocation();
  const [range, setRange] = useState<"30" | "90" | "180">("90");
  const [kind, setKind] = useState<"remission" | "flare">("remission");
  const [addingPeriod, setAddingPeriod] = useState(false);
  const [markingFlare, setMarkingFlare] = useState(false);

  const periods = useQuery({ queryKey: keys.periods, queryFn: api.periods });
  const days = useQuery({ queryKey: keys.days(Number(range)), queryFn: () => api.days(Number(range)) });
  const stress = useQuery({ queryKey: keys.stressPeriods, queryFn: api.stressPeriods });
  const decide = useMutation({ mutationFn: (v: { start: string; decision: "confirm" | "reject" }) => api.decidePeriod(v.start, v.decision), onSuccess: refresh });
  const remove = useMutation({ mutationFn: api.deleteStressPeriod, onSuccess: refresh });

  useEffect(() => {
    if (hash === "#periods" && stress.data) document.getElementById("periods")?.scrollIntoView({ behavior: "smooth" });
  }, [hash, stress.data]);

  if (periods.isLoading || !today) return <PageLoading />;
  if (periods.isError || !periods.data) return <LoadError onRetry={() => void periods.refetch()} />;
  const data = periods.data;
  const n = (v: number, d = 0): string => num(v, lang, d);
  const KindIcon = ({ k, className }: { k: Period["kind"]; className?: string }) => (k === "flare" ? <Flame className={className} /> : <Leaf className={className} />);
  const list = [...data.periods].reverse();

  return (
    <div>
      <PageTitle title={t("gut.title")} subtitle={t("gut.subtitle")} />

      {/* Current state */}
      <div className={cn("mb-4 flex items-center gap-3 rounded-3xl p-4", data.current_state === "flare" ? "bg-trigger text-white" : "bg-ok-soft text-ok")}>
        <span className={cn("grid h-11 w-11 shrink-0 place-items-center rounded-full", data.current_state === "flare" ? "bg-white/20" : "bg-ok text-white")}>
          <KindIcon k={data.current_state} className="h-5 w-5" />
        </span>
        <div>
          <p className="text-lg font-bold leading-snug">{t(`gut.now_${data.current_state}`)}</p>
          {data.periods.length > 0 && (
            <p className={cn("text-sm", data.current_state === "flare" ? "text-white/85" : "text-ink-soft")}>
              {t("gut.since", { date: shortDate(data.periods.at(-1)!.start, lang), days: n(data.periods.at(-1)!.days) })}
            </p>
          )}
        </div>
      </div>

      {/* Proposals the user must confirm (the user's answer always wins) */}
      {data.pending.map((p) => (
        <Card key={p.start} className="animate-rise mb-4 border-trigger/30 bg-trigger-soft">
          <p className="font-bold">{t("gut.proposal", { date: shortDate(p.start, lang) })}</p>
          <p className="mt-1 text-sm text-ink-soft">{t("gut.proposal_text", { index: data.index_name, at: n(data.thresholds.active_at), need: n(data.rules.active_days_needed), of: n(data.rules.window_days) })}</p>
          <div className="mt-3 flex gap-2">
            <Button size="sm" variant="danger" disabled={decide.isPending} onClick={() => decide.mutate({ start: p.start, decision: "confirm" })}>
              {t("gut.proposal_yes")}
            </Button>
            <Button size="sm" variant="outline" disabled={decide.isPending} onClick={() => decide.mutate({ start: p.start, decision: "reject" })}>
              {t("gut.proposal_no")}
            </Button>
          </div>
        </Card>
      ))}

      {/* Trend */}
      <Card className="p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 className="font-bold">{t("gut.trend", { index: data.index_name })}</h2>
          <div className="w-44">
            <Tabs value={range} onChange={setRange} tabs={[{ value: "30", label: n(30) }, { value: "90", label: n(90) }, { value: "180", label: t("gut.all") }]} />
          </div>
        </div>
        {days.data ? (
          days.data.days.length >= data.min_days ? (
            <>
              <TrendChart days={days.data.days} periods={data.periods} activeAt={data.thresholds.active_at} />
              <div className="mt-3">
                <PeriodStrip days={days.data.days} />
              </div>
              <p className="mt-3 text-xs text-ink-faint">{t("gut.chart_note", { index: data.index_name, at: n(data.thresholds.active_at) })}</p>
            </>
          ) : (
            <p className="py-8 text-center text-sm text-ink-soft">{t("gut.keep_logging", { need: n(data.min_days) })}</p>
          )
        ) : (
          <div className="skeleton h-56" />
        )}
      </Card>

      {/* Remission vs flare, kept apart */}
      <SectionTitle>{t("gut.compare")}</SectionTitle>
      <Tabs
        value={kind}
        onChange={setKind}
        tabs={[
          { value: "remission", label: <span className="inline-flex items-center gap-1.5"><Leaf className="h-4 w-4" />{t("gut.kind_remission")}</span> },
          { value: "flare", label: <span className="inline-flex items-center gap-1.5"><Flame className="h-4 w-4" />{t("gut.kind_flare")}</span> },
        ]}
      />
      <div className="animate-rise mt-3" key={kind}>
        <SummaryTiles s={data.summaries[kind]} indexName={data.index_name} />
        {data.summaries[kind].patterns_available && (
          <Link to="/patterns" className="mt-3 inline-block text-sm font-semibold text-brand">
            {t(`gut.patterns_in_${kind}`)} →
          </Link>
        )}
      </div>

      {kind === "flare" && data.before_flares.length > 0 && (
        <>
          <SectionTitle>{t("gut.before_flares")}</SectionTitle>
          <div className="space-y-2.5">
            {data.before_flares.map((b) => (
              <Card key={b.flare_start} className="p-4">
                <p className="font-bold">{t("gut.before_flare_of", { date: shortDate(b.flare_start, lang) })}</p>
                <p className="text-xs text-ink-faint">{t("gut.before_days", { n: n(b.days_logged) })}</p>
                {b.factors.length ? (
                  <ul className="mt-3 flex flex-wrap gap-2">
                    {b.factors.map((f) => (
                      <li key={f.factor} className="inline-flex items-center gap-1.5 rounded-full bg-paper-deep px-3 py-1.5 text-sm">
                        <FactorIcon factor={f.factor} className="h-3.5 w-3.5 text-ink-faint" />
                        {name(f.factor)}
                        <span className="tabular font-bold">×{n(f.count)}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm text-ink-soft">{t("gut.before_none")}</p>
                )}
              </Card>
            ))}
            <p className="px-1 text-xs text-ink-faint">{t("gut.before_note")}</p>
          </div>
        </>
      )}

      {/* Period list */}
      <SectionTitle
        action={
          <button type="button" className="text-sm font-semibold text-brand" onClick={() => setMarkingFlare(true)}>
            + {t("gut.mark_flare")}
          </button>
        }
      >
        {t("gut.periods")}
      </SectionTitle>
      {list.length ? (
        <Card className="divide-y divide-line/70 p-0">
          {list.map((p) => (
            <div key={`${p.kind}-${p.start}`} className="flex items-center gap-3 px-4 py-3">
              <span className={cn("grid h-9 w-9 shrink-0 place-items-center rounded-full", p.kind === "flare" ? "bg-trigger-soft text-trigger" : p.kind === "settling" ? "bg-saffron-soft text-caution" : "bg-ok-soft text-ok")}>
                <KindIcon k={p.kind} className="h-4 w-4" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="font-semibold">
                  {t(`gut.kind_${p.kind}`)}
                  {p.ongoing && <span className="ml-2 text-xs font-semibold text-ink-faint">· {t("gut.ongoing")}</span>}
                </p>
                <p className="text-xs text-ink-faint">
                  {dateRange(p.start, p.end, lang)} · {t("gut.n_days", { n: n(p.days) })}
                </p>
              </div>
              {p.kind === "flare" && (
                <Badge tone={p.status === "pending" ? "caution" : "neutral"}>
                  {p.status === "pending" ? t("gut.status_pending") : p.source === "user" ? t("gut.status_marked") : t("gut.status_confirmed")}
                </Badge>
              )}
            </div>
          ))}
        </Card>
      ) : (
        <Empty title={t("gut.keep_logging", { need: n(data.min_days) })} />
      )}

      {/* Stressful periods */}
      <div id="periods" className="scroll-mt-20">
        <SectionTitle
          action={
            <button type="button" className="text-sm font-semibold text-brand" onClick={() => setAddingPeriod(true)}>
              + {t("app.add")}
            </button>
          }
        >
          {t("gut.stress_periods")}
        </SectionTitle>
        <p className="mb-3 text-sm text-ink-soft">{t("gut.stress_periods_hint")}</p>
        {stress.data?.length ? (
          <Card className="divide-y divide-line/70 p-0">
            {[...stress.data].reverse().map((p) => {
              const until = daysBetween(today, p.start);
              return (
                <div key={p.id} className="flex items-center gap-3 px-4 py-3">
                  <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-brand-soft text-brand-deep">
                    {p.type === "exam" ? <GraduationCap className="h-4 w-4" /> : <CalendarPlus className="h-4 w-4" />}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-semibold">{p.name}</p>
                    <p className="text-xs text-ink-faint">
                      {t(`periodType.${p.type}`)} · {dateRange(p.start, p.end, lang)}
                    </p>
                  </div>
                  {until > 0 ? <Badge tone="brand">{t("gut.in_days", { n: n(until) })}</Badge> : p.end >= today ? <Badge tone="caution">{t("gut.now")}</Badge> : null}
                  <button type="button" aria-label={t("app.remove")} disabled={remove.isPending} onClick={() => remove.mutate(p.id)} className="rounded-full p-1.5 text-ink-faint hover:bg-paper-deep hover:text-trigger">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              );
            })}
          </Card>
        ) : (
          <Button variant="secondary" className="w-full" onClick={() => setAddingPeriod(true)}>
            <Plus className="h-4 w-4" />
            {t("gut.add_period")}
          </Button>
        )}
      </div>

      <p className="mt-8 rounded-3xl bg-paper-deep/70 p-4 text-sm text-ink-soft">{t("gut.footer", { index: data.index_name })}</p>

      <AddStressPeriod open={addingPeriod} onOpenChange={setAddingPeriod} today={today} />
      <MarkFlare open={markingFlare} onOpenChange={setMarkingFlare} today={today} />
    </div>
  );
}
