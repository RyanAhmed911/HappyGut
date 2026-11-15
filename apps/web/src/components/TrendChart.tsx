import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Area, AreaChart, CartesianGrid, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { num, shortDate } from "@/lib/format";
import type { DaySummary, Period } from "@/lib/schemas";
import { useLang } from "./shell";

export interface TrendChartProps {
  days: DaySummary[];
  periods: Period[];
  activeAt: number;
  height?: number;
}

/** Daily index with flare periods shaded and the "active disease" level as a dashed line. */
export default function TrendChart({ days, periods, activeAt, height = 220 }: TrendChartProps) {
  const { t } = useTranslation();
  const lang = useLang();
  const data = useMemo(() => days.map((d) => ({ date: d.date, index: d.index })), [days]);
  const first = data[0]?.date ?? "";
  const last = data.at(-1)?.date ?? "";
  const flares = periods.filter((p) => p.kind === "flare" && p.end >= first && p.start <= last);
  const max = Math.max(activeAt + 3, ...data.map((d) => d.index));
  const ticks = data.filter((_, i) => i % Math.ceil(data.length / 5) === 0).map((d) => d.date);
  return (
    <div style={{ height }} className="-ml-2">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
          <defs>
            <linearGradient id="indexFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-brand)" stopOpacity={0.35} />
              <stop offset="100%" stopColor="var(--color-brand)" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="var(--color-line)" strokeDasharray="3 4" />
          {flares.map((p) => (
            <ReferenceArea
              key={p.start}
              x1={p.start < first ? first : p.start}
              x2={p.end > last ? last : p.end}
              fill="var(--color-trigger)"
              fillOpacity={p.status === "pending" ? 0.08 : 0.14}
              stroke="var(--color-trigger)"
              strokeOpacity={0.25}
              strokeDasharray={p.status === "pending" ? "4 3" : undefined}
            />
          ))}
          <ReferenceLine y={activeAt} stroke="var(--color-trigger)" strokeDasharray="5 4" strokeOpacity={0.6} />
          <XAxis dataKey="date" ticks={ticks} tickFormatter={(d: string) => shortDate(d, lang)} tick={{ fontSize: 11, fill: "var(--color-ink-faint)" }} tickLine={false} axisLine={false} />
          <YAxis domain={[0, max]} allowDecimals={false} tick={{ fontSize: 11, fill: "var(--color-ink-faint)" }} tickFormatter={(v: number) => num(v, lang)} tickLine={false} axisLine={false} width={44} />
          <Tooltip
            cursor={{ stroke: "var(--color-ink-faint)", strokeDasharray: "3 3" }}
            content={({ active, payload }) => {
              const row = active ? (payload?.[0]?.payload as { date: string; index: number } | undefined) : undefined;
              if (!row) return null;
              return (
                <div className="rounded-xl border border-line bg-card px-3 py-2 text-xs shadow-card">
                  <p className="font-semibold">{shortDate(row.date, lang)}</p>
                  <p className="text-ink-soft">{t("gut.score_value", { value: num(row.index, lang) })}</p>
                </div>
              );
            }}
          />
          <Area type="monotone" dataKey="index" stroke="var(--color-brand)" strokeWidth={2.2} fill="url(#indexFill)" dot={false} activeDot={{ r: 4 }} isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
