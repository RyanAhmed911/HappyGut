import { useQuery } from "@tanstack/react-query";
import { Activity, FileText, FlaskConical, History, House, NotebookPen, ScanLine, Settings, Sparkles } from "lucide-react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link, NavLink, Outlet } from "react-router";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import { setLang, type Lang } from "@/lib/i18n";

export function useLang(): Lang {
  const { i18n } = useTranslation();
  return i18n.language === "en" ? "en" : "bn";
}

export function useProfile() {
  return useQuery({ queryKey: ["me"], queryFn: api.me, staleTime: 60_000 });
}

export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2 font-bold tracking-tight", className)}>
      <svg viewBox="0 0 64 64" className="h-8 w-8 shrink-0" aria-hidden>
        <rect width="64" height="64" rx="18" fill="var(--color-brand)" />
        <path
          d="M20 22c0-4 3-7 7-7h10c4 0 7 3 7 7s-3 7-7 7H27c-2.2 0-4 1.8-4 4s1.8 4 4 4h10c4 0 7 3 7 7s-3 7-7 7H24"
          fill="none"
          stroke="var(--color-paper)"
          strokeWidth="5"
          strokeLinecap="round"
        />
        <circle cx="46" cy="18" r="5" fill="var(--color-saffron)" />
      </svg>
      <span className="text-xl">HappyGut</span>
    </span>
  );
}

export function LangToggle({ className }: { className?: string }) {
  const lang = useLang();
  const { t } = useTranslation();
  return (
    <div role="group" aria-label={t("settings.language")} className={cn("inline-flex rounded-full border border-line bg-card p-0.5 text-sm font-semibold", className)}>
      {(["bn", "en"] as const).map((code) => (
        <button
          key={code}
          type="button"
          aria-pressed={lang === code}
          onClick={() => {
            setLang(code);
            void api.updateMe({ language: code }).catch(() => undefined);
          }}
          className={cn("rounded-full px-3 py-1 transition", lang === code ? "bg-brand text-white" : "text-ink-soft hover:text-ink")}
        >
          {code === "bn" ? "বাংলা" : "EN"}
        </button>
      ))}
    </div>
  );
}

export function SimulatedBadge({ className }: { className?: string }) {
  const { t } = useTranslation();
  return (
    <span
      title={t("app.simulated_long")}
      className={cn("inline-flex items-center gap-1 whitespace-nowrap rounded-full bg-saffron-soft px-2.5 py-1 text-xs font-semibold text-caution", className)}
    >
      <FlaskConical className="h-3.5 w-3.5" />
      {t("app.simulated_short")}
    </span>
  );
}

const NAV = [
  { to: "/", icon: House, key: "today", end: true },
  { to: "/check", icon: ScanLine, key: "check" },
  { to: "/diary", icon: NotebookPen, key: "diary" },
  { to: "/patterns", icon: Sparkles, key: "patterns" },
  { to: "/gut", icon: Activity, key: "gut" },
  { to: "/history", icon: History, key: "history" },
  { to: "/report", icon: FileText, key: "report" },
  { to: "/settings", icon: Settings, key: "settings" },
] as const;

function BottomLink({ to, icon: Icon, label, end }: { to: string; icon: typeof House; label: string; end?: boolean }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn("flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px] font-semibold transition", isActive ? "text-brand" : "text-ink-faint")
      }
    >
      <Icon className="h-[22px] w-[22px]" strokeWidth={2.2} />
      <span className="max-w-full truncate px-0.5">{label}</span>
    </NavLink>
  );
}

export function AppShell() {
  const { t } = useTranslation();
  const profile = useProfile();
  const simulated = profile.data?.is_synthetic;

  return (
    <div className="min-h-dvh">
      {/* Desktop side rail */}
      <aside className="no-print fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-line/70 bg-card/70 px-4 py-6 backdrop-blur lg:flex">
        <Link to="/" className="px-2">
          <Logo />
        </Link>
        <nav className="mt-8 flex flex-1 flex-col gap-1">
          {NAV.map(({ to, icon: Icon, key, ...rest }) => (
            <NavLink
              key={to}
              to={to}
              end={"end" in rest}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-2xl px-3 py-2.5 text-[15px] font-semibold transition",
                  isActive ? "bg-brand text-white shadow-float" : "text-ink-soft hover:bg-paper-deep/70",
                )
              }
            >
              <Icon className="h-5 w-5" />
              {t(`nav.${key}`)}
            </NavLink>
          ))}
        </nav>
        <div className="space-y-3 px-1">
          {simulated && <p className="rounded-2xl bg-saffron-soft p-3 text-xs leading-relaxed text-caution">{t("app.simulated_long")}</p>}
          <LangToggle />
        </div>
      </aside>

      {/* Phone top bar */}
      <header className="no-print sticky top-0 z-20 flex items-center justify-between gap-2 border-b border-line/60 bg-paper/85 px-4 py-2.5 backdrop-blur lg:hidden">
        <Link to="/">
          <Logo className="[&>span]:text-lg" />
        </Link>
        <div className="flex items-center gap-1.5">
          {simulated && <SimulatedBadge />}
          <LangToggle />
        </div>
      </header>

      <main className="lg:pl-64">
        <div className="mx-auto w-full max-w-3xl px-4 pb-28 pt-5 lg:px-8 lg:pb-12 lg:pt-10">
          <Outlet />
        </div>
      </main>

      {/* Phone bottom navigation with the meal check in the middle */}
      <nav className="no-print safe-bottom fixed inset-x-0 bottom-0 z-30 border-t border-line/70 bg-card/95 backdrop-blur lg:hidden">
        <div className="mx-auto flex max-w-md items-end px-2">
          <BottomLink to="/" end icon={House} label={t("nav.today")} />
          <BottomLink to="/diary" icon={NotebookPen} label={t("nav.diary")} />
          <NavLink to="/check" className="-mt-6 flex flex-1 flex-col items-center gap-0.5 pb-2 text-[11px] font-semibold text-brand" aria-label={t("nav.check")}>
            <span className="grid h-14 w-14 place-items-center rounded-full bg-brand text-white shadow-float ring-4 ring-paper">
              <ScanLine className="h-6 w-6" strokeWidth={2.4} />
            </span>
            <span>{t("nav.check_short")}</span>
          </NavLink>
          <BottomLink to="/patterns" icon={Sparkles} label={t("nav.patterns_short")} />
          <BottomLink to="/gut" icon={Activity} label={t("nav.gut")} />
        </div>
      </nav>
    </div>
  );
}

export function PageLoading({ children }: { children?: ReactNode }) {
  return (
    <div className="space-y-3" aria-busy>
      <div className="skeleton h-9 w-48" />
      <div className="skeleton h-32" />
      <div className="skeleton h-24" />
      {children}
    </div>
  );
}

export function LoadError({ onRetry }: { onRetry: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="rounded-3xl border border-trigger/20 bg-trigger-soft p-5 text-sm text-trigger">
      <p className="font-semibold">{t("app.error")}</p>
      <button type="button" className="mt-2 font-semibold underline" onClick={onRetry}>
        {t("app.retry")}
      </button>
    </div>
  );
}
