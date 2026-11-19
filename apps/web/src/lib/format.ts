/** Numbers and dates in the reader's language (Bangla digits and month names for bn). */
export type Lang = "bn" | "en";

const locale = (lang: string): string => (lang === "bn" ? "bn-BD" : "en-GB");

export function num(value: number, lang: string, digits = 0): string {
  return new Intl.NumberFormat(locale(lang), { minimumFractionDigits: 0, maximumFractionDigits: digits, useGrouping: false }).format(value);
}

export function pct(value: number, lang: string): string {
  return new Intl.NumberFormat(locale(lang), { style: "percent", maximumFractionDigits: 0 }).format(value);
}

/** "YYYY-MM-DD" → local Date at noon (avoids time-zone day shifts). */
export function parseDay(iso: string): Date {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y ?? 1970, (m ?? 1) - 1, d ?? 1, 12);
}

export function isoDay(date: Date): string {
  const p = (n: number): string => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${p(date.getMonth() + 1)}-${p(date.getDate())}`;
}

export function addDays(iso: string, days: number): string {
  const d = parseDay(iso);
  d.setDate(d.getDate() + days);
  return isoDay(d);
}

export function daysBetween(a: string, b: string): number {
  return Math.round((parseDay(b).getTime() - parseDay(a).getTime()) / 86_400_000);
}

export function shortDate(iso: string, lang: string): string {
  return new Intl.DateTimeFormat(locale(lang), { day: "numeric", month: "short" }).format(parseDay(iso));
}

export function longDate(iso: string, lang: string): string {
  return new Intl.DateTimeFormat(locale(lang), { weekday: "long", day: "numeric", month: "long" }).format(parseDay(iso));
}

export function dateRange(start: string, end: string, lang: string): string {
  return `${shortDate(start, lang)} – ${shortDate(end, lang)}`;
}

export function timeOfDay(iso: string, lang: string): string {
  return new Intl.DateTimeFormat(locale(lang), { hour: "numeric", minute: "2-digit" }).format(new Date(iso));
}

export function dayOfTimestamp(iso: string): string {
  return isoDay(new Date(iso));
}

/** "HH:MM" (24 h) → the reader's clock format. */
export function clock(hhmm: string, lang: string): string {
  const [h, m] = hhmm.split(":").map(Number);
  const d = new Date(2000, 0, 1, h ?? 0, m ?? 0);
  return new Intl.DateTimeFormat(locale(lang), { hour: "numeric", minute: "2-digit" }).format(d);
}

/** The current local time as "HH:MM" (24 h), the default time for a food added to the diary. */
export function nowClock(date: Date = new Date()): string {
  return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

/** The diary slot for an "HH:MM" time; mirrors the API's time_of_day_for. */
export function slotOf(hhmm: string): "morning" | "noon" | "afternoon" | "evening" | "night" {
  const hour = Number(hhmm.slice(0, 2));
  if (hour < 5 || hour >= 22) return "night";
  return hour < 11 ? "morning" : hour < 15 ? "noon" : hour < 18 ? "afternoon" : "evening";
}
