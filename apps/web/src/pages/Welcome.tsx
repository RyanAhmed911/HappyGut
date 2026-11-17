import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight, BookOpen, Eye, EyeOff, Info, LoaderCircle, Lock, Mail, Moon, ScanLine, ShieldCheck, Sparkles, User } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, Navigate, useNavigate } from "react-router";
import { LangToggle, Logo } from "@/components/shell";
import { Button, inputClass } from "@/components/ui";
import { VerdictDot } from "@/components/verdict";
import { api, ApiError, auth } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { VerdictCode } from "@/lib/schemas";

function PreviewRow({ verdict, name, why, delay }: { verdict: VerdictCode; name: string; why: string; delay: number }) {
  return (
    <div className="animate-rise flex items-center gap-3 rounded-xl bg-card px-3.5 py-3" style={{ animationDelay: `${delay}ms` }}>
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

  const form = (
    <form
      className="w-full max-w-sm"
      onSubmit={(e) => {
        e.preventDefault();
        login.mutate();
      }}
    >
      <h2 className="text-2xl font-bold tracking-tight">{t("welcome.sign_in")}</h2>
      <p className="mt-1 text-sm text-ink-soft">{t("welcome.sign_in_note")}</p>
      <label className="mt-6 block">
        <span className="mb-1.5 block text-sm font-semibold">{t("welcome.email")}</span>
        <span className="relative block">
          <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
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
      <label className="mt-4 block">
        <span className="mb-1.5 block text-sm font-semibold">{t("welcome.password")}</span>
        <span className="relative block">
          <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
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
            className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded-lg p-2 text-ink-faint hover:bg-paper-deep"
          >
            {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </span>
      </label>
      {error && (
        <p role="alert" className="mt-4 rounded-lg border border-trigger/20 bg-trigger-soft px-3.5 py-2.5 text-sm text-trigger">
          {error}
        </p>
      )}
      <Button type="submit" size="lg" className="mt-6 w-full" disabled={login.isPending || !email.trim() || !password}>
        {login.isPending && <LoaderCircle className="h-5 w-5 animate-spin" />}
        {t("welcome.sign_in")}
        <ArrowRight className="h-5 w-5" />
      </Button>
      <Link to="/about" className="mt-5 flex items-center justify-center gap-1.5 text-sm font-semibold text-brand hover:underline">
        <Info className="h-4 w-4" />
        {t("welcome.how_link")}
      </Link>
    </form>
  );

  return (
    <div className="min-h-dvh lg:grid lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
      {/* Brand panel */}
      <section className="relative overflow-hidden bg-brand-deep px-5 pb-24 pt-6 text-white lg:flex lg:min-h-dvh lg:flex-col lg:px-14 lg:py-10">
        <div aria-hidden className="pointer-events-none absolute -right-24 -top-24 h-80 w-80 rounded-full bg-brand/70 blur-2xl" />
        <div aria-hidden className="pointer-events-none absolute -bottom-32 -left-20 h-96 w-96 rounded-full bg-saffron/15 blur-3xl" />
        <div className="relative flex items-center justify-between">
          <Logo inverse />
          <LangToggle className="lg:hidden" />
        </div>

        <div className="relative mt-10 max-w-xl lg:my-auto lg:py-10">
          <p className="inline-flex items-center rounded-full border border-white/20 bg-white/10 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.12em] text-white/90">
            {t("welcome.kicker")}
          </p>
          <h1 className="mt-5 text-[34px] font-bold leading-[1.1] tracking-tight sm:text-5xl lg:text-[52px]">
            {t("welcome.title_1")} <span className="text-saffron">{t("welcome.title_2")}</span>
          </h1>
          <p className="mt-5 text-base text-white/80 lg:text-lg">{t("welcome.lead")}</p>

          {/* Illustration of a verdict, labelled as an example */}
          <div aria-label={t("welcome.example")} className="mt-8 hidden max-w-md rounded-2xl border border-white/15 bg-white/[0.07] p-3 lg:block">
            <p className="mb-2 px-1 text-[11px] font-bold uppercase tracking-[0.12em] text-white/60">{t("welcome.example")}</p>
            <div className="space-y-2 text-ink">
              <PreviewRow verdict="likely_trigger" name={t("welcome.ex_1_name")} why={t("welcome.ex_1_why")} delay={100} />
              <PreviewRow verdict="caution" name={t("welcome.ex_2_name")} why={t("welcome.ex_2_why")} delay={250} />
              <PreviewRow verdict="likely_ok" name={t("welcome.ex_3_name")} why={t("welcome.ex_3_why")} delay={400} />
            </div>
            <div className="mt-2 grid grid-cols-2 gap-2 text-[12px] font-semibold text-white/85">
              <span className="flex items-center gap-1.5 rounded-lg bg-white/10 px-2.5 py-2">
                <BookOpen className="h-3.5 w-3.5 text-saffron" />
                {t("welcome.ex_guideline")}
              </span>
              <span className="flex items-center gap-1.5 rounded-lg bg-white/10 px-2.5 py-2">
                <User className="h-3.5 w-3.5 text-saffron" />
                {t("welcome.ex_personal")}
              </span>
            </div>
          </div>
        </div>

        <ul className="relative hidden gap-x-8 gap-y-5 lg:grid lg:grid-cols-2">
          {features.map(({ icon: Icon, key }) => (
            <li key={key} className="flex gap-3">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-white/10 text-saffron">
                <Icon className="h-[18px] w-[18px]" />
              </span>
              <div>
                <p className="text-sm font-bold leading-snug">{t(`welcome.f_${key}_title`)}</p>
                <p className="text-[13px] leading-snug text-white/65">{t(`welcome.f_${key}_text`)}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      {/* Sign-in panel */}
      <section className="flex flex-col px-5 py-8 lg:min-h-dvh lg:px-14 lg:py-10">
        <div className="hidden justify-end lg:flex">
          <LangToggle />
        </div>
        <div className="flex flex-1 items-center justify-center">
          <div className="relative z-10 -mt-16 w-full max-w-sm rounded-2xl border border-line bg-card p-6 shadow-raised lg:mt-0 lg:border-0 lg:bg-transparent lg:p-0 lg:shadow-none">{form}</div>
        </div>

        <ul className="mt-10 grid gap-5 sm:grid-cols-2 lg:hidden">
          {features.map(({ icon: Icon, key }) => (
            <li key={key} className="flex gap-3">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-brand-soft text-brand-deep">
                <Icon className="h-5 w-5" />
              </span>
              <div>
                <p className="font-bold leading-snug">{t(`welcome.f_${key}_title`)}</p>
                <p className="text-sm text-ink-soft">{t(`welcome.f_${key}_text`)}</p>
              </div>
            </li>
          ))}
        </ul>

        <footer className="mx-auto mt-10 max-w-md text-center text-xs text-ink-faint">{t("app.disclaimer")}</footer>
      </section>
    </div>
  );
}
