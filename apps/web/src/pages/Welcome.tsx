import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight, BookOpen, Eye, EyeOff, LoaderCircle, Lock, Mail, Moon, ScanLine, ShieldCheck, Sparkles, User } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Navigate, useNavigate } from "react-router";
import { LangToggle, Logo } from "@/components/shell";
import { Button, inputClass } from "@/components/ui";
import { VerdictDot } from "@/components/verdict";
import { api, ApiError, auth } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { VerdictCode } from "@/lib/schemas";

function PreviewRow({ verdict, name, why, delay }: { verdict: VerdictCode; name: string; why: string; delay: number }) {
  return (
    <div className="animate-rise flex items-center gap-3 rounded-2xl bg-card p-3.5 shadow-card" style={{ animationDelay: `${delay}ms` }}>
      <VerdictDot verdict={verdict} />
      <div className="min-w-0">
        <p className="font-bold leading-snug">{name}</p>
        <p className="text-[13px] leading-snug text-ink-soft">{why}</p>
      </div>
    </div>
  );
}

export function Welcome() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const health = useQuery({ queryKey: ["health"], queryFn: api.health, retry: 1 });
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const login = useMutation({
    mutationFn: () => api.login(email.trim(), password),
    onSuccess: () => void navigate("/", { replace: true }),
  });
  const code = login.error instanceof ApiError ? login.error.code : "";
  const error = !login.isError
    ? health.isError
      ? t("welcome.server_down")
      : health.data?.sign_in === false
        ? t("welcome.sign_in_off")
        : null
    : code === "invalid_credentials"
      ? t("welcome.wrong_credentials")
      : code === "too_many_attempts"
        ? t("welcome.too_many_attempts")
        : t("welcome.server_down");
  if (auth.token) return <Navigate to="/" replace />;

  const features = [
    { icon: ScanLine, key: "check" },
    { icon: Moon, key: "diary" },
    { icon: Sparkles, key: "patterns" },
    { icon: ShieldCheck, key: "safety" },
  ] as const;

  return (
    <div className="relative min-h-dvh overflow-hidden">
      <div aria-hidden className="pointer-events-none absolute -left-32 -top-32 h-[420px] w-[420px] rounded-full bg-brand-soft/70 blur-3xl" />
      <div aria-hidden className="pointer-events-none absolute -bottom-40 -right-24 h-[460px] w-[460px] rounded-full bg-saffron-soft blur-3xl" />

      <div className="relative mx-auto flex min-h-dvh max-w-6xl flex-col px-5 py-6 lg:px-10">
        <header className="flex items-center justify-between">
          <Logo />
          <LangToggle />
        </header>

        <div className="grid flex-1 items-center gap-10 py-10 lg:grid-cols-[1.1fr_0.9fr] lg:gap-16">
          <section>
            <p className="inline-flex items-center gap-2 rounded-full bg-card px-3 py-1 text-xs font-bold uppercase tracking-[0.1em] text-brand shadow-card">
              {t("welcome.kicker")}
            </p>
            <h1 className="mt-5 text-[40px] font-bold leading-[1.08] tracking-tight sm:text-5xl lg:text-[58px]">
              {t("welcome.title_1")} <span className="text-brand">{t("welcome.title_2")}</span>
            </h1>
            <p className="mt-5 max-w-xl text-lg text-ink-soft">{t("welcome.lead")}</p>

            <form
              className="mt-8 max-w-md rounded-3xl border border-line/70 bg-card p-5 shadow-card"
              onSubmit={(e) => {
                e.preventDefault();
                login.mutate();
              }}
            >
              <p className="text-lg font-bold">{t("welcome.sign_in")}</p>
              <label className="mt-3 block">
                <span className="mb-1 block text-sm font-semibold text-ink-soft">{t("welcome.email")}</span>
                <span className="relative block">
                  <Mail className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
                  <input
                    type="text"
                    inputMode="email"
                    autoComplete="username"
                    autoCapitalize="none"
                    spellCheck={false}
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className={cn(inputClass, "pl-10")}
                  />
                </span>
              </label>
              <label className="mt-3 block">
                <span className="mb-1 block text-sm font-semibold text-ink-soft">{t("welcome.password")}</span>
                <span className="relative block">
                  <Lock className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
                  <input
                    type={show ? "text" : "password"}
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className={cn(inputClass, "px-10")}
                  />
                  <button
                    type="button"
                    onClick={() => setShow((v) => !v)}
                    aria-label={t(show ? "welcome.hide_password" : "welcome.show_password")}
                    className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full p-2 text-ink-faint hover:bg-paper-deep"
                  >
                    {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </span>
              </label>
              {error && (
                <p role="alert" className="mt-3 rounded-2xl bg-trigger-soft px-3.5 py-2 text-sm text-trigger">
                  {error}
                </p>
              )}
              <Button type="submit" size="lg" className="mt-4 w-full" disabled={login.isPending || !email.trim() || !password}>
                {login.isPending && <LoaderCircle className="h-5 w-5 animate-spin" />}
                {t("welcome.sign_in")}
                <ArrowRight className="h-5 w-5" />
              </Button>
              <p className="mt-3 text-center text-xs text-ink-faint">{t("welcome.sign_in_note")}</p>
            </form>

            <ul className="mt-10 grid gap-4 sm:grid-cols-2">
              {features.map(({ icon: Icon, key }) => (
                <li key={key} className="flex gap-3">
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-brand-soft text-brand-deep">
                    <Icon className="h-5 w-5" />
                  </span>
                  <div>
                    <p className="font-bold leading-snug">{t(`welcome.f_${key}_title`)}</p>
                    <p className="text-sm text-ink-soft">{t(`welcome.f_${key}_text`)}</p>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          {/* Illustration of a verdict, labelled as an example */}
          <section aria-label={t("welcome.example")} className="mx-auto w-full max-w-sm">
            <div className="rounded-[36px] border border-line bg-paper-deep/60 p-4 shadow-2xl shadow-brand/10">
              <div className="rounded-[26px] bg-paper p-4">
                <p className="mb-3 text-xs font-bold uppercase tracking-[0.1em] text-ink-faint">{t("welcome.example")}</p>
                <div className="space-y-2.5">
                  <PreviewRow verdict="likely_trigger" name={t("welcome.ex_1_name")} why={t("welcome.ex_1_why")} delay={100} />
                  <PreviewRow verdict="caution" name={t("welcome.ex_2_name")} why={t("welcome.ex_2_why")} delay={250} />
                  <PreviewRow verdict="likely_ok" name={t("welcome.ex_3_name")} why={t("welcome.ex_3_why")} delay={400} />
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-[12px] font-semibold text-ink-soft">
                  <span className="flex items-center gap-1.5 rounded-xl bg-brand-tint px-2.5 py-2">
                    <BookOpen className="h-3.5 w-3.5 text-brand" />
                    {t("welcome.ex_guideline")}
                  </span>
                  <span className="flex items-center gap-1.5 rounded-xl bg-saffron-soft px-2.5 py-2">
                    <User className="h-3.5 w-3.5 text-caution" />
                    {t("welcome.ex_personal")}
                  </span>
                </div>
              </div>
            </div>
          </section>
        </div>

        <footer className="pb-2 text-center text-xs text-ink-faint">{t("app.disclaimer")}</footer>
      </div>
    </div>
  );
}
