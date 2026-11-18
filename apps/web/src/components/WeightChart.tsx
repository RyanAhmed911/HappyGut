import { useTranslation } from "react-i18next";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { num, shortDate } from "@/lib/format";
import type { WeightPoint } from "@/lib/schemas";
import { useLang } from "./shell";

export interface WeightChartProps {
  entries: WeightPoint[];
  /** The weigh-in the loss is measured from, drawn as a dashed line. */
  peak?: WeightPoint | null;
  height?: number;
}

/** Weekly weigh-ins as a line, with the reference weight for a loss shown dashed. */
export default function WeightChart({ entries, peak, height = 160 }: WeightChartProps) {
  const { t } = useTranslation();
  const lang = useLang();
  const values = entries.map((e) => e.kg);
  const lo = Math.floor(Math.min(...values) - 1);
  const hi = Math.ceil(Math.max(...values) + 1);
  const ticks = entries.filter((_, i) => i % Math.max(1, Math.ceil(entries.length / 4)) === 0).map((e) => e.date);
  return (
    <div style={{ height }} className="-ml-2">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={entries} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
          <CartesianGrid vertical={false} stroke="var(--color-line)" strokeDasharray="3 4" />
          {peak && <ReferenceLine y={peak.kg} stroke="var(--color-caution)" strokeDasharray="5 4" strokeOpacity={0.7} />}
          <XAxis dataKey="date" ticks={ticks} tickFormatter={(d: string) => shortDate(d, lang)} tick={{ fontSize: 11, fill: "var(--color-ink-faint)" }} tickLine={false} axisLine={false} />
          <YAxis domain={[lo, hi]} allowDecimals={false} tick={{ fontSize: 11, fill: "var(--color-ink-faint)" }} tickFormatter={(v: number) => num(v, lang)} tickLine={false} axisLine={false} width={44} />
          <Tooltip
            cursor={{ stroke: "var(--color-ink-faint)", strokeDasharray: "3 3" }}
            content={({ active, payload }) => {
              const row = active ? (payload?.[0]?.payload as WeightPoint | undefined) : undefined;
              if (!row) return null;
              return (
                <div className="rounded-lg border border-line bg-card px-3 py-2 text-xs shadow-card">
                  <p className="font-semibold">{shortDate(row.date, lang)}</p>
                  <p className="text-ink-soft">{t("weight.kg", { value: num(row.kg, lang, 1) })}</p>
                </div>
              );
            }}
          />
          <Line type="monotone" dataKey="kg" stroke="var(--color-brand)" strokeWidth={2.2} dot={{ r: 2.5, fill: "var(--color-brand)" }} activeDot={{ r: 4 }} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
