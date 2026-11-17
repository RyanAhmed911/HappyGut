import { useQuery } from "@tanstack/react-query";
import { Activity, FileText, History, House, Info, LogOut, NotebookPen, Salad, ScanLine, Settings, Sparkles } from "lucide-react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link, NavLink, Outlet, useLocation } from "react-router";
import { api, auth } from "@/lib/api";
import { isoDay, longDate } from "@/lib/format";
import { cn } from "@/lib/cn";
import { DataNotice } from "./notice";
import { useDiaryReminder } from "@/lib/reminder";
import { setLang, type Lang } from "@/lib/i18n";

export function useLang(): Lang {
  const { i18n } = useTranslation();
  return i18n.language === "en" ? "en" : "bn";
}

export function useProfile() {
  return useQuery({ queryKey: ["me"], queryFn: api.me, staleTime: 60_000 });
}

export function Logo({ className, inverse }: { className?: string; inverse?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2 font-bold tracking-tight", className)}>
      <svg viewBox="0 0 64 64" className="h-8 w-8 shrink-0" aria-hidden>
        <rect width="64" height="64" rx="16" fill={inverse ? "#ffffff" : "var(--color-brand)"} />
        <path
          d="M20 22c0-4 3-7 7-7h10c4 0 7 3 7 7s-3 7-7 7H27c-2.2 0-4 1.8-4 4s1.8 4 4 4h10c4 0 7 3 7 7s-3 7-7 7H24"
          fill="none"
          stroke={inverse ? "var(--color-brand)" : "#ffffff"}
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
    <div role="group" aria-label={t("settings.language")} className={cn("inline-flex rounded-lg border border-line bg-card p-0.5 text-[13px] font-semibold", className)}>
      {(["bn", "en"] as const).map((code) => (
        <button
          key={code}
          type="button"
          aria-pressed={lang === code}
          onClick={() => {
            setLang(code);
            void api.updateMe({ language: code }).catch(() => undefined);
          }}
          className={cn("rounded-md px-2.5 py-1 transition", lang === code ? "bg-brand text-white" : "text-ink-soft hover:text-ink")}
        >
          {code === "bn" ? "বাংলা" : "EN"}
        </button>
      ))}
    </div>
  );
}

type NavItem = { to: string; icon: typeof House; key: string; end?: boolean };
const NAV_GROUPS: { key: string; items: NavItem[] }[] = [
  {
    key: "daily",
    items: [
      { to: "/", icon: House, key: "today", end: true },
      { to: "/check", icon: ScanLine, key: "check" },
      { to: "/diary", icon: NotebookPen, key: "diary" },
    ],
  },
  {
    key: "insights",
    items: [
      { to: "/patterns", icon: Sparkles, key: "patterns" },
      { to: "/gut", icon: Activity, key: "gut" },
      { to: "/foods", icon: Salad, key: "foods" },
    ],
  },
  {
    key: "records",
    items: [
      { to: "/history", icon: History, key: "history" },
      { to: "/report", icon: FileText, key: "report" },
    ],
  },
];
const FOOTER_NAV: NavItem[] = [
  { to: "/about", icon: Info, key: "about" },
  { to: "/settings", icon: Settings, key: "settings" },
];

/** Pages that use the full desktop width; the rest read better as a single column. */
const WIDE = new Set(["/", "/patterns", "/gut", "/foods", "/check"]);

export function signOut(): void {
  auth.clear();
  window.dispatchEvent(new Event("hg:signed-out"));
}

function initials(name: string): string {
  return Array.from(name.trim())[0]?.toUpperCase() ?? "?";
}

export function Avatar({ name, className }: { name: string; className?: string }) {
  return (
    <span aria-hidden className={cn("grid h-9 w-9 shrink-0 place-items-center rounded-full bg-brand text-sm font-bold text-white", className)}>
      {initials(name)}
    </span>
  );
}

function SideLink({ to, icon: Icon, label, end }: { to: string; icon: typeof House; label: string; end?: boolean }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-semibold transition",
          isActive ? "bg-brand-tint text-brand-deep" : "text-ink-soft hover:bg-paper hover:text-ink",
        )
      }
    >
      {({ isActive }) => (
        <>
          <span aria-hidden className={cn("absolute inset-y-1.5 left-0 w-[3px] rounded-full transition", isActive ? "bg-brand" : "bg-transparent")} />
          <Icon className={cn("h-[18px] w-[18px]", isActive ? "text-brand" : "text-ink-faint group-hover:text-ink-soft")} strokeWidth={2.1} />
          {label}
        </>
      )}
    </NavLink>
  );
}

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
  const lang = useLang();
  const profile = useProfile();
  const { pathname } = useLocation();
  useDiaryReminder(profile.data?.reminder_time);
  const me = profile.data;
  const dx = me ? t(`today.dx_${me.diagnosis}`) : "";
  const wide = WIDE.has(pathname);

  return (
    <div className="min-h-dvh">
      {/* Desktop side rail */}
      <aside className="no-print fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-line bg-card lg:flex">
        <Link to="/" className="flex h-16 items-center px-5">
          <Logo />
        </Link>
        <nav className="flex flex-1 flex-col gap-5 overflow-y-auto px-3 pb-3 pt-2">
          {NAV_GROUPS.map((group) => (
            <div key={group.key}>
              <p className="mb-1 px-3 text-[11px] font-bold uppercase tracking-[0.1em] text-ink-faint">{t(`nav.group_${group.key}`)}</p>
              <div className="flex flex-col gap-0.5">
                {group.items.map((item) => (
                  <SideLink key={item.to} to={item.to} icon={item.icon} label={t(`nav.${item.key}`)} end={item.end} />
                ))}
              </div>
            </div>
          ))}
          <div className="mt-auto flex flex-col gap-0.5 border-t border-line pt-3">
            {FOOTER_NAV.map((item) => (
              <SideLink key={item.to} to={item.to} icon={item.icon} label={t(`nav.${item.key}`)} />
            ))}
          </div>
        </nav>
        {me && (
          <div className="flex items-center gap-3 border-t border-line px-4 py-3">
            <Avatar name={me.display_name} />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-bold leading-tight">{me.display_name}</p>
              <p className="truncate text-xs text-ink-faint">{dx}</p>
            </div>
            <button
              type="button"
              onClick={signOut}
              title={t("settings.sign_out")}
              aria-label={t("settings.sign_out")}
              className="rounded-lg p-2 text-ink-faint transition hover:bg-paper hover:text-ink"
            >
              <LogOut className="h-[18px] w-[18px]" />
            </button>
          </div>
        )}
      </aside>

      {/* Top bar: brand on phones, context and actions on desktop */}
      <header className="no-print sticky top-0 z-20 border-b border-line bg-paper/85 backdrop-blur lg:ml-64">
        <div className="flex h-14 items-center justify-between gap-3 px-4 lg:h-16 lg:px-8">
          <Link to="/" className="lg:hidden">
            <Logo className="[&>span]:text-lg" />
          </Link>
          <div className="hidden min-w-0 items-center gap-3 lg:flex">
            <p className="truncate text-sm font-medium text-ink-soft">{longDate(isoDay(new Date()), lang)}</p>
            {me && (
              <span
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold",
                  me.state === "flare" ? "bg-trigger-soft text-trigger" : "bg-ok-soft text-ok",
                )}
              >
                <span className={cn("h-1.5 w-1.5 rounded-full", me.state === "flare" ? "bg-trigger" : "bg-ok")} />
                {t(`nav.state_${me.state}`)}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2.5">
            {pathname !== "/check" && (
              <Link
                to="/check"
                className="hidden h-9 items-center gap-2 rounded-lg bg-brand px-3.5 text-sm font-semibold text-white shadow-float transition hover:bg-brand-deep lg:inline-flex"
              >
                <ScanLine className="h-4 w-4" strokeWidth={2.4} />
                {t("nav.check")}
              </Link>
            )}
            <LangToggle />
            {me && (
              <Link to="/settings" aria-label={t("nav.settings")} className="lg:hidden">
                <Avatar name={me.display_name} className="h-8 w-8 text-[13px]" />
              </Link>
            )}
          </div>
        </div>
      </header>

      {me?.is_synthetic && <DataNotice />}

      <main className="lg:pl-64">
        <div className={cn("mx-auto w-full px-4 pb-28 pt-5 lg:px-8 lg:pb-14 lg:pt-8", wide ? "max-w-6xl" : pathname.startsWith("/diary") ? "max-w-2xl" : "max-w-3xl")}>
          <Outlet />
        </div>
      </main>

      {/* Phone bottom navigation with the meal check in the middle */}
      <nav className="no-print safe-bottom fixed inset-x-0 bottom-0 z-30 border-t border-line bg-card/95 backdrop-blur lg:hidden">
        <div className="mx-auto flex max-w-md items-end px-2">
          <BottomLink to="/" end icon={House} label={t("nav.today")} />
          <BottomLink to="/diary" icon={NotebookPen} label={t("nav.diary")} />
          <NavLink to="/check" className="-mt-6 flex flex-1 flex-col items-center gap-0.5 pb-2 text-[11px] font-semibold text-brand" aria-label={t("nav.check")}>
            <span className="grid h-14 w-14 place-items-center rounded-full bg-brand text-white shadow-raised ring-4 ring-paper">
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
    <div className="rounded-2xl border border-trigger/20 bg-trigger-soft p-5 text-sm text-trigger">
      <p className="font-semibold">{t("app.error")}</p>
      <button type="button" className="mt-2 font-semibold underline" onClick={onRetry}>
        {t("app.retry")}
      </button>
    </div>
  );
}
