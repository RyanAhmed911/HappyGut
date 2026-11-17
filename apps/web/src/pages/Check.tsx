import { useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, Camera, ImagePlus, LoaderCircle, Moon, RotateCcw, Send, ShieldCheck, ThumbsDown, ThumbsUp, UtensilsCrossed, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { useLang } from "@/components/shell";
import { Button, Card, Chip, PageTitle } from "@/components/ui";
import { Escalation, MealResult, VerdictDot } from "@/components/verdict";
import { api, ApiError } from "@/lib/api";
import { cn } from "@/lib/cn";
import { DishesEvent, ExplanationEvent, RedFlag, VerdictEvent } from "@/lib/schemas";

type Stage =
  | { name: "idle" }
  | { name: "working"; dishes?: string[]; verdict?: VerdictEvent; explanation?: ExplanationEvent }
  | { name: "done"; verdict: VerdictEvent; explanation?: ExplanationEvent; id: string }
  | { name: "red_flag"; flag: RedFlag }
  | { name: "message"; kind: "not_food" | "error"; text: string };

const EXAMPLES = ["ex_1", "ex_2", "ex_3", "ex_4"] as const;

export function Check() {
  const { t } = useTranslation();
  const lang = useLang();
  const queryClient = useQueryClient();
  const health = useQuery({ queryKey: ["health"], queryFn: api.health });
  const [text, setText] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [stage, setStage] = useState<Stage>({ name: "idle" });
  const [feedback, setFeedback] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const cameraRef = useRef<HTMLInputElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!photo) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(photo);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [photo]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const reset = (): void => {
    setStage({ name: "idle" });
    setText("");
    setPhoto(null);
    setFeedback(null);
  };

  const submit = async (): Promise<void> => {
    if (!text.trim() && !photo) return;
    const form = new FormData();
    if (text.trim()) form.set("text", text.trim());
    if (photo) form.set("image", photo);
    form.set("lang", lang);
    setFeedback(null);
    setStage({ name: "working" });
    abortRef.current = new AbortController();
    let finished = false;
    try {
      await api.mealCheck(
        form,
        ({ event, data }) => {
          if (event === "dishes") {
            const parsed = DishesEvent.parse(data);
            setStage((s) => (s.name === "working" ? { ...s, dishes: parsed.dishes.map((d) => d.name) } : s));
          } else if (event === "verdict") {
            const verdict = VerdictEvent.parse(data);
            setStage((s) => (s.name === "working" ? { ...s, verdict } : s));
          } else if (event === "explanation") {
            const explanation = ExplanationEvent.parse(data);
            setStage((s) => (s.name === "working" ? { ...s, explanation } : s));
          } else if (event === "done") {
            finished = true;
            const id = (data as { meal_check_id: string }).meal_check_id;
            setStage((s) => (s.name === "working" && s.verdict ? { name: "done", verdict: s.verdict, explanation: s.explanation, id } : s));
          } else if (event === "red_flag") {
            finished = true;
            setStage({ name: "red_flag", flag: RedFlag.parse(data) });
          } else if (event === "not_food") {
            finished = true;
            setStage({ name: "message", kind: "not_food", text: (data as { message: string }).message });
          } else if (event === "error") {
            finished = true;
            const code = (data as { code: string }).code;
            setStage({ name: "message", kind: "error", text: t(code === "perception_unavailable" ? "check.err_photo_unavailable" : "app.error") });
          }
        },
        abortRef.current.signal,
      );
      if (!finished) setStage({ name: "message", kind: "error", text: t("app.error") });
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      const code = error instanceof ApiError ? error.code : "";
      const key = code === "image_too_large" ? "check.err_too_large" : code === "not_an_image" || code === "unsupported_image_type" ? "check.err_not_image" : "app.error";
      setStage({ name: "message", kind: "error", text: t(key) });
    } finally {
      void queryClient.invalidateQueries({ queryKey: ["mealChecks"] });
      void queryClient.invalidateQueries({ queryKey: ["diary"] });
    }
  };

  const sendFeedback = (id: string, answer: "right" | "wrong" | "not_sure"): void => {
    setFeedback(answer);
    void api.feedback(id, answer).catch(() => setFeedback(null));
  };

  // ------------------------------------------------------------ result views

  if (stage.name === "red_flag") {
    return (
      <div className="mx-auto max-w-md pt-2">
        <Escalation flag={stage.flag} onClose={reset} />
      </div>
    );
  }

  if (stage.name === "working" || stage.name === "done") {
    const { verdict, explanation } = stage;
    return (
      <div className="mx-auto max-w-3xl">
        <PageTitle title={t("check.result_title")} />
        {preview && <img src={preview} alt="" className="mb-3 h-40 w-full rounded-2xl object-cover" />}

        {!verdict && (
          <Card className="animate-rise">
            <div className="flex items-center gap-3">
              <LoaderCircle className="h-5 w-5 animate-spin text-brand" />
              <p className="font-semibold">{stage.name === "working" && stage.dishes ? t("check.step_judging") : t("check.step_looking")}</p>
            </div>
            {stage.name === "working" && stage.dishes && (
              <div className="mt-3 flex flex-wrap gap-2">
                {stage.dishes.map((d, i) => (
                  <span key={`${d}-${i}`} className="animate-pop rounded-full bg-brand-soft px-3 py-1 text-sm font-semibold text-brand-deep" style={{ animationDelay: `${i * 90}ms` }}>
                    {d}
                  </span>
                ))}
              </div>
            )}
            <div className="mt-4 space-y-2">
              <div className="skeleton h-4 w-3/4" />
              <div className="skeleton h-4 w-1/2" />
            </div>
          </Card>
        )}

        {verdict && <MealResult verdict={verdict} explanation={explanation} />}

        {stage.name === "done" && (
          <div className="animate-rise mt-5 space-y-3">
            <Card className="p-4">
              <p className="text-sm font-semibold">{t("check.feedback_q")}</p>
              {feedback ? (
                <p className="mt-2 text-sm text-ok">{t("check.feedback_thanks")}</p>
              ) : (
                <div className="mt-2.5 flex flex-wrap gap-2">
                  <Chip onClick={() => sendFeedback(stage.id, "right")}>
                    <ThumbsUp className="h-4 w-4" />
                    {t("check.feedback_right")}
                  </Chip>
                  <Chip onClick={() => sendFeedback(stage.id, "wrong")}>
                    <ThumbsDown className="h-4 w-4" />
                    {t("check.feedback_wrong")}
                  </Chip>
                  <Chip onClick={() => sendFeedback(stage.id, "not_sure")}>{t("check.feedback_unsure")}</Chip>
                </div>
              )}
            </Card>
            <p className="px-1 text-center text-sm text-ink-soft">{t("check.logged")}</p>
            <div className="grid gap-2.5 sm:grid-cols-2">
              <Button variant="outline" onClick={reset}>
                <RotateCcw className="h-4 w-4" />
                {t("check.another")}
              </Button>
              <Link to="/diary" className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-brand px-4 text-sm font-semibold text-white shadow-float transition hover:bg-brand-deep">
                <Moon className="h-4 w-4" />
                {t("check.to_diary")}
              </Link>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ------------------------------------------------------------ input view

  const photoOff = health.data && !health.data.models.perception;
  return (
    <div>
      <PageTitle title={t("check.title")} subtitle={t("check.subtitle")} />

      {stage.name === "message" && (
        <div className={cn("animate-rise mb-4 flex gap-3 rounded-2xl p-4 text-[15px]", stage.kind === "error" ? "bg-trigger-soft text-trigger" : "bg-unsure-soft text-unsure")}>
          <UtensilsCrossed className="mt-0.5 h-5 w-5 shrink-0" />
          <p>{stage.text}</p>
        </div>
      )}

      <div className="lg:grid lg:grid-cols-12 lg:items-start lg:gap-x-6">
      <div className="lg:col-span-7">
      <input ref={cameraRef} type="file" accept="image/*" capture="environment" hidden onChange={(e) => setPhoto(e.target.files?.[0] ?? null)} />
      <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={(e) => setPhoto(e.target.files?.[0] ?? null)} />

      {preview ? (
        <div className="relative overflow-hidden rounded-2xl shadow-card">
          <img src={preview} alt={t("check.photo_alt")} className="h-56 w-full object-cover" />
          <button type="button" onClick={() => setPhoto(null)} aria-label={t("app.remove")} className="absolute right-3 top-3 grid h-9 w-9 place-items-center rounded-full bg-ink/70 text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => cameraRef.current?.click()}
            className="flex flex-col items-center gap-2 rounded-2xl border-2 border-dashed border-brand/30 bg-brand-tint px-4 py-7 text-brand-deep transition hover:border-brand active:scale-[0.98]"
          >
            <span className="grid h-14 w-14 place-items-center rounded-full bg-brand text-white shadow-float">
              <Camera className="h-6 w-6" />
            </span>
            <span className="font-bold">{t("check.take_photo")}</span>
            <span className="text-center text-xs text-ink-soft">{t("check.take_photo_hint")}</span>
          </button>
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className="flex flex-col items-center gap-2 rounded-2xl border-2 border-dashed border-line bg-card px-4 py-7 text-ink-soft transition hover:border-brand/50 active:scale-[0.98]"
          >
            <span className="grid h-14 w-14 place-items-center rounded-full bg-paper-deep">
              <ImagePlus className="h-6 w-6" />
            </span>
            <span className="font-bold text-ink">{t("check.choose_photo")}</span>
            <span className="text-center text-xs">{t("check.choose_photo_hint")}</span>
          </button>
        </div>
      )}
      {photoOff && <p className="mt-2 rounded-xl bg-caution-soft px-3.5 py-2 text-xs text-caution">{t("check.photo_off")}</p>}

      <div className="my-5 flex items-center gap-3 text-xs font-semibold uppercase tracking-[0.1em] text-ink-faint">
        <span className="h-px flex-1 bg-line" />
        {t("check.or_type")}
        <span className="h-px flex-1 bg-line" />
      </div>

      <label className="block">
        <span className="sr-only">{t("check.text_label")}</span>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
          maxLength={1000}
          placeholder={t("check.placeholder")}
          className="w-full resize-none rounded-2xl border border-line bg-card p-4 text-base outline-none transition placeholder:text-ink-faint focus:border-brand focus:ring-4 focus:ring-brand/10"
        />
      </label>
      <div className="mt-2.5 flex flex-wrap gap-2">
        {EXAMPLES.map((key) => (
          <Chip key={key} className="min-h-9 text-[13px]" onClick={() => setText(t(`check.${key}`))}>
            {t(`check.${key}`)}
          </Chip>
        ))}
      </div>

      <Button size="lg" className="mt-6 w-full" disabled={!text.trim() && !photo} onClick={() => void submit()}>
        <Send className="h-5 w-5" />
        {t("check.submit")}
      </Button>
      <p className="mt-3 text-center text-xs text-ink-faint">{t("check.privacy")}</p>
      </div>

      <aside className="mt-8 lg:col-span-5 lg:mt-0">
        <Card>
          <h2 className="font-bold">{t("check.legend_title")}</h2>
          <ul className="mt-3 space-y-3">
            {(["likely_ok", "caution", "likely_trigger", "not_sure"] as const).map((v) => (
              <li key={v} className="flex items-start gap-3">
                <VerdictDot verdict={v} className="mt-0.5 h-8 w-8" />
                <div>
                  <p className="text-sm font-bold leading-snug">{t(`verdict.${v}`)}</p>
                  <p className="text-[13px] leading-snug text-ink-soft">{t(`check.legend_${v}`)}</p>
                </div>
              </li>
            ))}
          </ul>
          <div className="mt-4 space-y-2 border-t border-line pt-4 text-[13px] text-ink-soft">
            <p className="flex gap-2">
              <BookOpen className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
              {t("check.legend_sources")}
            </p>
            <p className="flex gap-2">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
              {t("check.legend_engine")}
            </p>
          </div>
        </Card>
      </aside>
      </div>
    </div>
  );
}
