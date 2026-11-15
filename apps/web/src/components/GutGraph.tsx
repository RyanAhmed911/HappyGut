import { useTranslation } from "react-i18next";
import type { Pattern } from "@/lib/schemas";
import { useFactorName } from "./insights";

const COLOR = {
  likely_contributor: "var(--color-trigger)",
  possible: "var(--color-saffron)",
  not_linked: "var(--color-ok)",
  not_enough_data: "var(--color-ink-faint)",
} as const;

/**
 * The Personal Gut Graph: the person in the middle, one node per food type or habit.
 * Edge thickness and node size grow with how strongly the factor is linked to worse days.
 */
export function GutGraph({ patterns, name }: { patterns: Pattern[]; name: string }) {
  const { t } = useTranslation();
  const label = useFactorName();
  const nodes = patterns.filter((p) => p.label !== "not_enough_data").slice(0, 12);
  const size = 360;
  const c = size / 2;
  const split = (text: string): string[] => {
    const words = text.split(" ");
    if (words.length < 3) return [text];
    const mid = Math.ceil(words.length / 2);
    return [words.slice(0, mid).join(" "), words.slice(mid).join(" ")];
  };
  return (
    <figure>
      <svg viewBox={`0 0 ${size} ${size}`} className="mx-auto w-full max-w-md" role="img" aria-label={t("patterns.graph_title")}>
        {nodes.map((p, i) => {
          const angle = (i / nodes.length) * 2 * Math.PI - Math.PI / 2;
          const linked = p.label === "likely_contributor" || p.label === "possible";
          const radius = linked ? 118 : 138;
          const x = c + radius * Math.cos(angle);
          const y = c + radius * Math.sin(angle);
          const r = 9 + p.probability * 11;
          const lines = split(label(p.factor));
          const below = y >= c;
          return (
            <g key={p.factor}>
              <line
                x1={c}
                y1={c}
                x2={x}
                y2={y}
                stroke={COLOR[p.label]}
                strokeWidth={linked ? 1.5 + p.probability * 4 : 1}
                strokeOpacity={linked ? 0.55 : 0.25}
                strokeDasharray={p.label === "possible" ? "5 4" : undefined}
                strokeLinecap="round"
              />
              <circle cx={x} cy={y} r={r} fill={COLOR[p.label]} fillOpacity={linked ? 0.92 : 0.5} />
              <text x={x} y={y + 3.5} textAnchor="middle" className="fill-white text-[9px] font-bold">
                {Math.round(p.probability * 100)}
              </text>
              {lines.map((line, k) => (
                <text
                  key={k}
                  x={x}
                  y={below ? y + r + 11 + k * 10 : y - r - 5 - (lines.length - 1 - k) * 10}
                  textAnchor="middle"
                  className="fill-ink-soft text-[9px] font-semibold"
                >
                  {line}
                </text>
              ))}
            </g>
          );
        })}
        <circle cx={c} cy={c} r={34} fill="var(--color-brand)" />
        <circle cx={c} cy={c} r={41} fill="none" stroke="var(--color-brand)" strokeOpacity={0.25} strokeWidth={3} />
        <text x={c} y={c + 4} textAnchor="middle" className="fill-white text-[12px] font-bold">
          {name.slice(0, 9)}
        </text>
      </svg>
      <figcaption className="mt-3 flex flex-wrap justify-center gap-x-4 gap-y-1 text-xs text-ink-soft">
        {(["likely_contributor", "possible", "not_linked"] as const).map((k) => (
          <span key={k} className="inline-flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: COLOR[k] }} />
            {t(`patterns.label_${k}`)}
          </span>
        ))}
        <span className="basis-full text-center text-ink-faint">{t("patterns.graph_note")}</span>
      </figcaption>
    </figure>
  );
}
