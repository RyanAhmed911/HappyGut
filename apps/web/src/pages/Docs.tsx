import { useQuery } from "@tanstack/react-query";
import { ArrowDown, ArrowRight, CalendarClock, Check, Copy, Download, Eye, Lock, Mail, Printer, Radio, RotateCw, Search } from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { LangToggle, Logo, useLang } from "@/components/shell";
import { Badge, Card, Skeleton } from "@/components/ui";
import evaluation from "@/data/evaluation.json";
import { CHANGELOG, FEATURE_LABELS, SECTIONS, sectionText, type DocLang, type DocSection } from "@/data/docsContent";
import { cn } from "@/lib/cn";
import { DocsError, docsApi, type DocsLive, type DocsPage } from "@/lib/docs";
import { num } from "@/lib/format";

type L = { en: string; bn: string };
const pick = (text: L, lang: DocLang): string => text[lang];

export function dhakaTime(iso: string, lang: DocLang, withDate = true): string {
  return new Intl.DateTimeFormat(lang === "bn" ? "bn-BD" : "en-GB", {
    timeZone: "Asia/Dhaka",
    ...(withDate ? { day: "numeric", month: "short", year: "numeric" } : {}),
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(iso));
}

function duration(seconds: number, lang: DocLang): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return lang === "bn" ? `${num(h, lang)} ঘণ্টা ${num(m, lang)} মিনিট` : `${h} h ${m} min`;
}

/** Admin-replaced text: blank lines separate paragraphs, lines starting with "- " become bullet points. */
function RichText({ text }: { text: string }) {
  const blocks = text.split(/\n\s*\n/).map((b) => b.trim()).filter(Boolean);
  return (
    <div className="space-y-3">
      {blocks.map((block, i) => {
        const lines = block.split("\n").map((l) => l.trim()).filter(Boolean);
        if (lines.every((l) => l.startsWith("- "))) {
          return (
            <ul key={i} className="space-y-2">
              {lines.map((l, j) => (
                <Bullet key={j}>{l.slice(2)}</Bullet>
              ))}
            </ul>
          );
        }
        return (
          <p key={i} className="text-[15px] leading-relaxed text-ink-soft">
            {lines.join(" ")}
          </p>
        );
      })}
    </div>
  );
}

function Bullet({ children }: { children: ReactNode }) {
  return (
    <li className="flex gap-2.5 text-[15px] leading-relaxed text-ink-soft">
      <span aria-hidden className="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand" />
      <span>{children}</span>
    </li>
  );
}

function Tile({ value, label, note }: { value: string; label: string; note?: string }) {
  return (
    <div className="rounded-xl border border-line bg-card p-3.5">
      <p className="tabular text-xl font-bold tracking-tight text-brand-deep">{value}</p>
      <p className="mt-0.5 text-[13px] font-semibold leading-snug">{label}</p>
      {note && <p className="mt-0.5 text-xs text-ink-faint">{note}</p>}
    </div>
  );
}

const STATUS_TONE: Record<string, string> = {
  live: "bg-brand-soft text-brand-deep",
  template: "bg-saffron-soft text-caution",
  off: "bg-paper-deep text-ink-faint",
  built: "bg-unsure-soft text-unsure",
  planned: "bg-paper-deep text-ink-soft",
};

// ------------------------------------------------------------------ live widgets

function Features({ live, lang }: { live: DocsLive; lang: DocLang }) {
  const { t } = useTranslation();
  return (
    <div className="overflow-hidden rounded-xl border border-line">
      <table className="w-full text-left text-sm">
        <thead className="bg-paper-deep/60 text-xs uppercase tracking-wide text-ink-faint">
          <tr>
            <th className="px-3.5 py-2.5 font-semibold">{t("docs.feature")}</th>
            <th className="px-3.5 py-2.5 text-right font-semibold">{t("docs.status")}</th>
          </tr>
        </thead>
        <tbody>
          {live.features.map((f) => (
            <tr key={f.id} className="border-t border-line bg-card">
              <td className="px-3.5 py-2.5">{FEATURE_LABELS[f.id] ? pick(FEATURE_LABELS[f.id]!, lang) : f.id}</td>
              <td className="px-3.5 py-2.5 text-right">
                <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold", STATUS_TONE[f.status])}>{t(`docs.state_${f.status}`)}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Box({ title, children, tone = "plain" }: { title: string; children?: ReactNode; tone?: "plain" | "brand" | "ai" | "guard" }) {
  const tones = {
    plain: "border-line bg-card",
    brand: "border-brand/40 bg-brand-tint",
    ai: "border-unsure/30 bg-unsure-soft/60",
    guard: "border-caution/30 bg-saffron-soft/70",
  };
  return (
    <div className={cn("rounded-xl border p-3", tones[tone])}>
      <p className="text-sm font-bold leading-snug">{title}</p>
      {children && <div className="mt-1 text-xs leading-relaxed text-ink-soft">{children}</div>}
    </div>
  );
}

const Down = () => <ArrowDown aria-hidden className="mx-auto my-1.5 h-4 w-4 text-ink-faint" />;

function Architecture({ live, lang }: { live: DocsLive; lang: DocLang }) {
  const bn = lang === "bn";
  const n = (v: number): string => num(v, lang);
  return (
    <div role="img" aria-label={bn ? "HappyGut-এর কাঠামোর নকশা" : "HappyGut architecture diagram"} className="rounded-2xl border border-line bg-paper p-3.5">
      <Box title={bn ? "ফোন · React PWA (Vercel)" : "Phone · React PWA (Vercel)"}>{bn ? "বাংলা ও ইংরেজি, ইনস্টলযোগ্য" : "Bangla and English, installable"}</Box>
      <Down />
      <div className="rounded-xl border border-brand/40 bg-card p-3">
        <p className="text-sm font-bold">{bn ? "FastAPI এপিআই (Render) · HTTPS · SSE" : "FastAPI API (Render) · HTTPS · SSE"}</p>
        <div className="mt-2.5 grid gap-2 sm:grid-cols-2">
          <Box tone="guard" title={bn ? "খাবার যাচাই (LangGraph)" : "Meal check (LangGraph)"}>
            {bn
              ? "বিপদ সংকেত → ব্যক্তিগত তথ্য মোছা → এআই পড়া → জ্ঞানভান্ডার → ইঞ্জিনের সিদ্ধান্ত → এআই ব্যাখ্যা + যাচাই"
              : "Red flags → PII scrub → AI perception → knowledge graph → engine decides → AI explains + guard"}
          </Box>
          <Box tone="brand" title={bn ? "ব্যক্তিগত স্তর" : "Personal layer"}>
            {bn
              ? "ডায়েরি · প্যাটার্ন ফাইন্ডার · রেমিশন/ফ্লেয়ার · ফ্লেয়ার ঝুঁকি v0 + LightGBM v1 · ওজন · ওষুধ"
              : "Diary · Pattern Finder · remission/flare · flare risk v0 + LightGBM v1 · weight · medicines"}
          </Box>
        </div>
      </div>
      <Down />
      <div className="grid gap-2 sm:grid-cols-3">
        <Box tone="ai" title={bn ? "এআই মডেল" : "AI models"}>
          {live.model_names.perception?.[0] ?? "Gemini"} · {live.model_names.explanation?.at(-1) ?? "Groq"}
        </Box>
        <Box title={bn ? "জ্ঞানভান্ডার" : "Knowledge"}>
          {bn
            ? `${n(live.knowledge.dishes)}টি খাবার · ${n(live.knowledge.rule_cards)}টি নিয়ম-কার্ড (YAML → গ্রাফ)`
            : `${live.knowledge.dishes} dishes · ${live.knowledge.rule_cards} Rule Cards (YAML → graph)`}
        </Box>
        <Box title={bn ? "সংরক্ষণ" : "Storage"}>
          {bn ? "প্রোটোটাইপ: মেমরিতে · আসল ব্যবহারকারী: Supabase Postgres (প্রস্তুত)" : "Prototype: in memory · real users: Supabase Postgres (prepared)"}
        </Box>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Box title="n8n">{bn ? "নির্ধারিত কাজ" : "scheduled jobs"}</Box>
        <Box title="Langfuse">{bn ? "ট্রেস" : "traces"}</Box>
        <Box title={bn ? "৪টি MCP সার্ভার" : "4 MCP servers"}>{bn ? "এআই ক্লায়েন্টের জন্য" : "for AI clients"}</Box>
        <Box title={bn ? "জিপিইউ কাজ" : "GPU jobs"}>{bn ? "অফলাইন, git দিয়ে" : "offline, via git"}</Box>
      </div>
    </div>
  );
}

const FLOW: { title: L; text: L; tone: "plain" | "brand" | "ai" | "guard" }[] = [
  { title: { en: "1 · Input", bn: "১ · ইনপুট" }, text: { en: "Photo of a plate, label or menu, or text in Bangla or English", bn: "প্লেট, মোড়ক বা মেনুর ছবি, অথবা বাংলা বা ইংরেজিতে লেখা" }, tone: "plain" },
  { title: { en: "2 · Safety first", bn: "২ · আগে নিরাপত্তা" }, text: { en: "Red-flag check on the raw text; a warning sign stops here and shows the escalation screen", bn: "মূল লেখায় বিপদ সংকেত খোঁজা; সংকেত থাকলে এখানেই থেমে জরুরি পরামর্শের পাতা" }, tone: "guard" },
  { title: { en: "3 · Privacy", bn: "৩ · গোপনীয়তা" }, text: { en: "Personal details removed; photo checked and stripped of location data", bn: "ব্যক্তিগত তথ্য মোছা; ছবি যাচাই ও অবস্থানের তথ্য সরানো" }, tone: "guard" },
  { title: { en: "4 · AI reads", bn: "৪ · এআই পড়ে" }, text: { en: "Gemini returns the dishes as JSON (typed names are matched without a model)", bn: "Gemini খাবারগুলো JSON আকারে দেয় (লেখা নাম মডেল ছাড়াই মেলে)" }, tone: "ai" },
  { title: { en: "5 · Knowledge + you", bn: "৫ · জ্ঞানভান্ডার + আপনি" }, text: { en: "Dish → components → Rule Cards for this patient, plus their own diary patterns", bn: "খাবার → উপাদান → এই রোগীর নিয়ম-কার্ড, সঙ্গে তাঁর নিজের ডায়েরির প্যাটার্ন" }, tone: "plain" },
  { title: { en: "6 · Engine decides", bn: "৬ · ইঞ্জিন সিদ্ধান্ত নেয়" }, text: { en: "Deterministic, tested verdict per dish; stricture rules first; no evidence → not sure", bn: "প্রতিটি খাবারে নির্দিষ্ট, পরীক্ষিত মতামত; আগে স্ট্রিকচারের নিয়ম; প্রমাণ না থাকলে নিশ্চিত নই" }, tone: "brand" },
  { title: { en: "7 · AI explains", bn: "৭ · এআই ব্যাখ্যা করে" }, text: { en: "The why in Bangla or English, checked against the verdict", bn: "বাংলা বা ইংরেজিতে কারণ, মতামতের সঙ্গে মিলিয়ে দেখা" }, tone: "ai" },
  { title: { en: "8 · Output", bn: "৮ · ফলাফল" }, text: { en: "Verdict cards streamed to the phone, with citations and a gentler option", bn: "সূত্র ও হালকা বিকল্পসহ মতামতের কার্ড ফোনে ধাপে ধাপে আসে" }, tone: "plain" },
];

function DataFlow({ lang }: { lang: DocLang }) {
  const bn = lang === "bn";
  return (
    <div className="rounded-2xl border border-line bg-paper p-3.5">
      <ol className="grid gap-2 sm:grid-cols-2">
        {FLOW.map((step) => (
          <li key={step.title.en}>
            <Box tone={step.tone} title={pick(step.title, lang)}>
              {pick(step.text, lang)}
            </Box>
          </li>
        ))}
      </ol>
      <div className="mt-2.5 flex items-start gap-2.5 rounded-xl bg-brand-deep p-3 text-white">
        <RotateCw aria-hidden className="mt-0.5 h-4 w-4 shrink-0" />
        <p className="text-xs leading-relaxed text-white/85">
          <span className="font-bold text-white">{bn ? "৯ · ফিডব্যাক: " : "9 · Feedback: "}</span>
          {bn
            ? "ডায়েরিতে যোগ করা খাবার → রাতের ডায়েরি → প্যাটার্ন ফাইন্ডার → ব্যক্তিগত প্রমাণ আবার ধাপ ৫-এ ফেরে, তাই পরের মতামত এই মানুষটির জন্য আরও ব্যক্তিগত হয়।"
            : "Added meals → nightly diary → Pattern Finder → personal evidence flows back into step 5, so the next verdict is more personal."}
        </p>
      </div>
    </div>
  );
}

function Endpoints({ live }: { live: DocsLive }) {
  const { t } = useTranslation();
  const method: Record<string, string> = { GET: "text-brand-deep", POST: "text-unsure", PUT: "text-caution", PATCH: "text-caution", DELETE: "text-trigger" };
  return (
    <div className="overflow-x-auto rounded-xl border border-line">
      <table className="w-full min-w-[480px] text-left text-sm">
        <thead className="bg-paper-deep/60 text-xs uppercase tracking-wide text-ink-faint">
          <tr>
            <th className="px-3 py-2.5 font-semibold">{t("docs.method")}</th>
            <th className="px-3 py-2.5 font-semibold">{t("docs.path")}</th>
            <th className="px-3 py-2.5 text-right font-semibold">{t("docs.access")}</th>
          </tr>
        </thead>
        <tbody className="font-mono text-[13px]">
          {live.endpoints.map((e) => (
            <tr key={`${e.method} ${e.path}`} className="border-t border-line bg-card">
              <td className={cn("px-3 py-2 font-bold", method[e.method])}>{e.method}</td>
              <td className="px-3 py-2 break-all">{e.path}</td>
              <td className="px-3 py-2 text-right font-sans text-xs text-ink-soft">{t(`docs.access_${e.access}`)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Usage({ live, lang }: { live: DocsLive; lang: DocLang }) {
  const { t } = useTranslation();
  if (!live.usage) return <p className="text-sm text-ink-faint">{t("docs.usage_none")}</p>;
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
      {Object.entries(live.usage).map(([key, value]) => (
        <Tile key={key} value={num(value, lang)} label={t(`docs.usage_${key}`)} />
      ))}
    </div>
  );
}

function Results({ lang }: { lang: DocLang }) {
  const { t } = useTranslation();
  const e = evaluation;
  const last = e.cohort.horizons[e.cohort.horizons.length - 1]!;
  const n = (v: number): string => num(v, lang);
  return (
    <div className="grid gap-2 sm:grid-cols-3">
      <Tile value={`${n(last.found)}/${n(last.of)}`} label={t("docs.result_patterns")} note={t("docs.result_patterns_note", { patients: n(e.cohort.patients) })} />
      <Tile value={`${n(e.red_flags.caught)}/${n(e.red_flags.phrases)}`} label={t("docs.result_red_flags")} note={t("docs.result_red_flags_note", { n: n(e.red_flags.false_alarms), of: n(e.red_flags.ordinary) })} />
      <Tile value={`${n(e.verdicts.identical)}/${n(e.verdicts.assessments)}`} label={t("docs.result_verdicts")} note={t("docs.result_verdicts_note", { dishes: n(e.verdicts.dishes) })} />
    </div>
  );
}

function AiLive({ live, lang }: { live: DocsLive; lang: DocLang }) {
  const { t } = useTranslation();
  const card = live.flare_model;
  const n = (v: number, d = 3): string => num(v, lang, d);
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      <div className="rounded-xl border border-line bg-card p-3.5 text-sm">
        <p className="font-bold">{t("docs.models_now")}</p>
        <p className="mt-1 text-ink-soft">
          {t("docs.models_perception")}: {live.models.perception ? (live.model_names.perception ?? []).join(" → ") : t("docs.state_off")}
        </p>
        <p className="mt-0.5 text-ink-soft">
          {t("docs.models_explanation")}: {live.models.explanation ? (live.model_names.explanation ?? []).join(" → ") : t("docs.state_template")}
        </p>
        <p className="mt-0.5 text-ink-soft">
          {t("docs.engine")}: {live.engine_version}
        </p>
      </div>
      {card && (
        <div className="rounded-xl border border-line bg-card p-3.5 text-sm">
          <p className="font-bold">
            {t("docs.flare_model")} · {card.version}
          </p>
          <p className="mt-1 text-ink-soft">{t("docs.flare_auc", { v1: n(card.v1.roc_auc), v0: n(card.v0.roc_auc) })}</p>
          <p className="mt-0.5 text-ink-soft">
            {t("docs.flare_caught", { v1: num(card.v1.top_10_percent.caught, lang), v0: num(card.v0.top_10_percent.caught, lang), of: num(card.v1.top_10_percent.of, lang) })}
          </p>
          <p className="mt-1 text-xs text-ink-faint">{t("docs.simulated_note")}</p>
        </div>
      )}
    </div>
  );
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]!.toUpperCase())
    .join("");
}

function TeamGrid({ page, lang }: { page: DocsPage; lang: DocLang }) {
  const { t } = useTranslation();
  return (
    <div>
      <p className="mb-3 text-sm font-semibold text-ink-soft">{t("docs.team_name", { name: page.team.name })}</p>
      <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {page.team.members.map((m) => (
          <li key={m.name} className="flex flex-col items-center rounded-2xl border border-line bg-card p-4 text-center">
            {m.photo_url ? (
              <img src={m.photo_url} alt={m.name} width={96} height={96} className="h-24 w-24 rounded-full border-2 border-brand-soft object-cover" loading="lazy" referrerPolicy="no-referrer" />
            ) : (
              <span aria-hidden className="grid h-24 w-24 place-items-center rounded-full border-2 border-brand-soft bg-brand-tint text-xl font-bold text-brand-deep">
                {initials(m.name)}
              </span>
            )}
            <p className="mt-3 font-bold leading-snug">{m.name}</p>
            <p className="mt-0.5 text-sm text-ink-soft">{(lang === "bn" && m.role_bn) || m.role || t("docs.role_unset")}</p>
            {m.email && (
              <a href={`mailto:${m.email}`} className="mt-1.5 inline-flex items-center gap-1 break-all text-xs font-semibold text-brand hover:underline">
                <Mail className="h-3.5 w-3.5 shrink-0" />
                {m.email}
              </a>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

function Demo({ live }: { live: DocsLive }) {
  const { t } = useTranslation();
  return (
    <div className="space-y-2">
      {live.accounts.map((a) => (
        <div key={a.email} className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-line bg-card px-3.5 py-2.5 text-sm">
          <span className="font-mono text-[13px] font-semibold">{a.email}</span>
          <span className="text-ink-soft">{a.role}</span>
        </div>
      ))}
      <Link to="/welcome" className="inline-flex h-10 items-center gap-1.5 rounded-lg bg-brand px-4 text-sm font-semibold text-white shadow-float hover:bg-brand-deep print:hidden">
        {t("docs.try_app")} <ArrowRight className="h-4 w-4" />
      </Link>
      <p className="text-xs text-ink-faint">{t("docs.passwords_note")}</p>
    </div>
  );
}

function Changelog({ page, lang }: { page: DocsPage; lang: DocLang }) {
  const { t } = useTranslation();
  return (
    <div>
      <ol className="relative space-y-3 border-l-2 border-line pl-4">
        {CHANGELOG.map((c) => (
          <li key={c.date} className="relative">
            <span aria-hidden className="absolute -left-[23px] top-1.5 h-3 w-3 rounded-full border-2 border-card bg-brand" />
            <p className="tabular text-xs font-semibold text-ink-faint">{new Intl.DateTimeFormat(lang === "bn" ? "bn-BD" : "en-GB", { dateStyle: "medium" }).format(new Date(`${c.date}T12:00:00Z`))}</p>
            <p className="text-sm text-ink-soft">{pick(c.text, lang)}</p>
          </li>
        ))}
      </ol>
      {page.updated_at && <p className="mt-3 text-xs text-ink-faint">{t("docs.edited_at", { at: dhakaTime(page.updated_at, lang) })}</p>}
    </div>
  );
}

function Widget({ id, page, lang }: { id: string; page: DocsPage; lang: DocLang }) {
  const live = page.live;
  switch (id) {
    case "demo":
      return <Demo live={live} />;
    case "traction":
      return (
        <div className="space-y-3">
          <Results lang={lang} />
          <Usage live={live} lang={lang} />
        </div>
      );
    case "team":
      return <TeamGrid page={page} lang={lang} />;
    case "features":
      return <Features live={live} lang={lang} />;
    case "architecture":
      return <Architecture live={live} lang={lang} />;
    case "data_flow":
      return <DataFlow lang={lang} />;
    case "api":
      return <Endpoints live={live} />;
    case "ai_layer":
      return <AiLive live={live} lang={lang} />;
    case "analytics":
      return <Usage live={live} lang={lang} />;
    case "changelog":
      return <Changelog page={page} lang={lang} />;
    default:
      return null;
  }
}

// ------------------------------------------------------------------ export

function markdown(page: DocsPage, lang: DocLang, ordered: DocSection[]): string {
  const live = page.live;
  const out = [`# HappyGut`, "", `${lang === "bn" ? "টিম" : "Team"} ${page.team.name} · v${live.version} · ${live.engine_version} · ${dhakaTime(live.served_at, lang)}`, ""];
  for (const section of ordered) {
    out.push(`## ${pick(section.title, lang)}`, "");
    const override = page.sections[section.id];
    out.push(override ? override[lang] : sectionText(section, lang), "");
    if (section.id === "team") page.team.members.forEach((m) => {
        const role = (lang === "bn" && m.role_bn) || m.role;
        out.push(`- ${m.name}${role ? ` · ${role}` : ""}${m.email ? ` · ${m.email}` : ""}`);
      });
    if (section.id === "features") live.features.forEach((f) => out.push(`- ${FEATURE_LABELS[f.id] ? pick(FEATURE_LABELS[f.id]!, lang) : f.id}: ${f.status}`));
    if (section.id === "api") live.endpoints.forEach((e) => out.push(`- \`${e.method} ${e.path}\` (${e.access})`));
    if (section.id === "changelog") CHANGELOG.forEach((c) => out.push(`- ${c.date}: ${pick(c.text, lang)}`));
    if (["team", "features", "api", "changelog"].includes(section.id)) out.push("");
  }
  return out.join("\n");
}

function download(name: string, text: string, type: string): void {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

// ------------------------------------------------------------------ page

function DocsHeader({ onMarkdown }: { onMarkdown?: () => void }) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const copy = async (): Promise<void> => {
    try {
      await navigator.clipboard.writeText(`${window.location.origin}/docs`);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard blocked: nothing to do */
    }
  };
  const btn = "inline-flex h-9 items-center gap-1.5 rounded-lg border border-line bg-card px-2.5 text-[13px] font-semibold hover:border-ink-faint/50";
  return (
    <header className="sticky top-0 z-20 border-b border-line bg-paper/85 backdrop-blur print:static print:border-0">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-2 px-4 lg:h-16">
        <Link to="/docs" className="flex items-center gap-2">
          <Logo className="[&>span]:text-lg" />
          <span className="hidden rounded-md bg-brand-soft px-1.5 py-0.5 text-xs font-bold text-brand-deep sm:inline">/docs</span>
        </Link>
        <div className="flex items-center gap-1.5 print:hidden">
          {onMarkdown && (
            <>
              <button type="button" onClick={onMarkdown} className={btn} aria-label={t("docs.export_md")}>
                <Download className="h-4 w-4" />
                <span className="hidden md:inline">{t("docs.export_md")}</span>
              </button>
              <button type="button" onClick={() => window.print()} className={btn} aria-label={t("docs.export_pdf")}>
                <Printer className="h-4 w-4" />
                <span className="hidden md:inline">{t("docs.export_pdf")}</span>
              </button>
              <button type="button" onClick={() => void copy()} className={btn} aria-label={t("docs.copy_link")}>
                {copied ? <Check className="h-4 w-4 text-brand" /> : <Copy className="h-4 w-4" />}
                <span className="hidden md:inline">{copied ? t("docs.copied") : t("docs.copy_link")}</span>
              </button>
            </>
          )}
          <LangToggle />
        </div>
      </div>
    </header>
  );
}

function Unavailable() {
  const { t } = useTranslation();
  const lang = useLang();
  const status = useQuery({ queryKey: ["docsStatus"], queryFn: docsApi.status });
  const s = status.data;
  return (
    <Card className="mx-auto mt-10 max-w-lg p-6 text-center">
      <span className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-paper-deep text-ink-soft">
        <Lock className="h-5 w-5" />
      </span>
      <h1 className="mt-4 text-xl font-bold">{t("docs.unavailable_title")}</h1>
      <p className="mt-2 text-sm text-ink-soft">{s ? t(`docs.unavailable_${s.reason === "open" ? "off" : s.reason}`) : t("docs.unavailable_off")}</p>
      {s && (s.starts_at || s.ends_at) && (
        <p className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-paper-deep px-3 py-1.5 text-xs font-semibold text-ink-soft">
          <CalendarClock className="h-4 w-4" />
          {s.starts_at ? dhakaTime(s.starts_at, lang) : "…"} – {s.ends_at ? dhakaTime(s.ends_at, lang) : "…"}
        </p>
      )}
      <div className="mt-5 flex justify-center gap-2">
        <Link to="/about" className="inline-flex h-10 items-center rounded-lg border border-line px-4 text-sm font-semibold">
          {t("docs.how_it_works")}
        </Link>
        <Link to="/welcome" className="inline-flex h-10 items-center rounded-lg bg-brand px-4 text-sm font-semibold text-white">
          {t("docs.try_app")}
        </Link>
      </div>
    </Card>
  );
}

export function Docs() {
  const { t } = useTranslation();
  const lang = useLang();
  const [query, setQuery] = useState("");
  const page = useQuery({ queryKey: ["docsPage"], queryFn: docsApi.page, refetchInterval: 60_000, retry: (n, e) => !(e instanceof DocsError && e.status === 403) && n < 2 });
  const data = page.data;

  const ordered = useMemo(() => {
    if (!data) return [];
    const byId = new Map(SECTIONS.map((s) => [s.id, s]));
    return [...data.order.pitch, ...data.order.tech].map((id) => byId.get(id)).filter((s): s is DocSection => Boolean(s));
  }, [data]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q || !data) return ordered;
    return ordered.filter((s) => {
      const text = `${pick(s.title, lang)} ${data.sections[s.id]?.[lang] ?? sectionText(s, lang)}`.toLowerCase();
      return text.includes(q);
    });
  }, [ordered, query, data, lang]);

  if (page.error instanceof DocsError && page.error.status === 403) {
    return (
      <div className="min-h-dvh">
        <DocsHeader />
        <main className="px-4">
          <Unavailable />
        </main>
      </div>
    );
  }

  const live = data?.live;
  const n = (v: number): string => num(v, lang);

  return (
    <div className="min-h-dvh">
      <DocsHeader onMarkdown={data ? () => download(`happygut-docs-${lang}.md`, markdown(data, lang, ordered), "text/markdown") : undefined} />
      {data?.preview && (
        <div className="bg-saffron-soft px-4 py-2 text-center text-sm font-semibold text-caution print:hidden">
          <Eye className="mr-1.5 inline h-4 w-4" />
          {t("docs.preview_banner")}
        </div>
      )}
      <div className="mx-auto max-w-6xl px-4 pb-20 pt-6 lg:grid lg:grid-cols-[230px_minmax(0,1fr)] lg:gap-10 lg:pt-10">
        {/* Section navigation */}
        <aside className="print:hidden lg:sticky lg:top-24 lg:h-[calc(100dvh-7rem)] lg:overflow-y-auto">
          <label className="relative block">
            <span className="sr-only">{t("docs.search")}</span>
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("docs.search")}
              className="h-10 w-full rounded-lg border border-line bg-card pl-9 pr-3 text-sm outline-none focus:border-brand focus:ring-4 focus:ring-brand/12"
            />
          </label>
          <nav aria-label={t("docs.contents")} className="mt-3 flex gap-1.5 overflow-x-auto pb-2 lg:block lg:space-y-4 lg:overflow-visible">
            {(["pitch", "tech"] as const).map((part) => (
              <div key={part} className="contents lg:block">
                <p className="hidden px-2 text-[11px] font-bold uppercase tracking-wider text-ink-faint lg:block">{t(`docs.part_${part}`)}</p>
                <ul className="contents lg:mt-1 lg:block lg:space-y-0.5">
                  {visible
                    .filter((s) => s.part === part)
                    .map((s) => (
                      <li key={s.id} className="shrink-0">
                        <a href={`#s-${s.id}`} className="block whitespace-nowrap rounded-lg border border-line bg-card px-2.5 py-1.5 text-[13px] font-medium text-ink-soft hover:text-brand lg:border-0 lg:bg-transparent lg:px-2 lg:py-1">
                          {pick(s.title, lang)}
                        </a>
                      </li>
                    ))}
                </ul>
              </div>
            ))}
          </nav>
        </aside>

        <main className="min-w-0">
          {/* Cover */}
          <section className="rounded-3xl bg-brand-deep p-6 text-white sm:p-8">
            <p className="inline-flex items-center gap-1.5 rounded-full bg-white/12 px-2.5 py-1 text-xs font-semibold">
              <Radio className="h-3.5 w-3.5 text-saffron" />
              {live ? t("docs.live_at", { at: dhakaTime(live.served_at, lang) }) : t("docs.loading")}
            </p>
            <h1 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">{t("docs.title")}</h1>
            <p className="mt-2 max-w-2xl text-[15px] leading-relaxed text-white/80">{t("docs.subtitle")}</p>
            <p className="mt-3 text-sm font-semibold text-white/90">{data ? t("docs.team_name", { name: data.team.name }) : " "}</p>
            <div className="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
              {live ? (
                [
                  [n(live.knowledge.dishes), t("docs.stat_dishes")],
                  [n(live.knowledge.rule_cards), t("docs.stat_rules")],
                  [n(live.endpoints.length), t("docs.stat_endpoints")],
                  [duration(live.uptime_s, lang), t("docs.stat_uptime")],
                ].map(([value, label]) => (
                  <div key={label} className="rounded-xl bg-white/10 p-3">
                    <p className="tabular text-lg font-bold">{value}</p>
                    <p className="text-xs text-white/75">{label}</p>
                  </div>
                ))
              ) : (
                <Skeleton className="col-span-full h-16 bg-white/10" />
              )}
            </div>
          </section>

          {page.isPending && (
            <div className="mt-6 space-y-3">
              <Skeleton className="h-40" />
              <Skeleton className="h-40" />
            </div>
          )}
          {page.isError && !(page.error instanceof DocsError && page.error.status === 403) && (
            <Card className="mt-6 p-5 text-sm text-ink-soft">{t("docs.load_error")}</Card>
          )}

          {data && visible.length === 0 && <p className="mt-8 text-center text-sm text-ink-faint">{t("docs.no_results")}</p>}

          {data &&
            visible.map((section, i) => {
              const firstTech = section.part === "tech" && visible[i - 1]?.part !== "tech";
              const override = data.sections[section.id];
              return (
                <div key={section.id}>
                  {(i === 0 || firstTech) && (
                    <p className="mt-10 text-xs font-bold uppercase tracking-wider text-brand">{t(`docs.part_${section.part}`)}</p>
                  )}
                  <section id={`s-${section.id}`} className="scroll-mt-24 border-b border-line py-7 last:border-0 print:break-inside-avoid">
                    <h2 className="text-2xl font-bold tracking-tight">
                      <a href={`#s-${section.id}`} className="hover:text-brand">
                        {pick(section.title, lang)}
                      </a>
                    </h2>
                    <div className="mt-3">
                      {override ? (
                        <RichText text={override[lang]} />
                      ) : (
                        <>
                          <p className="text-[15px] leading-relaxed text-ink-soft">{pick(section.lead, lang)}</p>
                          {section.points[lang].length > 0 && (
                            <ul className="mt-3 space-y-2">
                              {section.points[lang].map((p) => (
                                <Bullet key={p}>{p}</Bullet>
                              ))}
                            </ul>
                          )}
                        </>
                      )}
                    </div>
                    <div className="mt-4 empty:hidden">
                      <Widget id={section.id} page={data} lang={lang} />
                    </div>
                  </section>
                </div>
              );
            })}

          {data && (
            <footer className="mt-10 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-5 text-xs text-ink-faint">
              <span>{t("app.disclaimer")}</span>
              <span className="inline-flex items-center gap-2">
                <Badge tone="brand">v{data.live.version}</Badge>
                <Link to="/docs/admin" className="font-semibold hover:text-brand print:hidden">
                  {t("docs.admin_link")}
                </Link>
              </span>
            </footer>
          )}
        </main>
      </div>
    </div>
  );
}
