import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, Globe, LogOut, RotateCcw, ShieldCheck, Stethoscope } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { LangToggle, useLang, useProfile } from "@/components/shell";
import { Button, Card, inputClass, PageTitle, SectionTitle, Segmented, Toggle } from "@/components/ui";
import { api, auth } from "@/lib/api";
import { num } from "@/lib/format";
import { PERSONAL_KEYS } from "@/lib/hooks";
import { reminder } from "@/lib/reminder";
import { PHENOTYPES, type Phenotype } from "@/lib/schemas";

export function SettingsPage() {
  const { t } = useTranslation();
  const lang = useLang();
  const queryClient = useQueryClient();
  const profile = useProfile();
  const health = useQuery({ queryKey: ["health"], queryFn: api.health });
  const [notify, setNotify] = useState(reminder.enabled());
  const [blocked, setBlocked] = useState(false);
  const update = useMutation({
    mutationFn: api.updateMe,
    onSuccess: (data) => {
      queryClient.setQueryData(["me"], data);
      for (const key of PERSONAL_KEYS) if (key[0] !== "me") void queryClient.invalidateQueries({ queryKey: [...key] });
    },
  });
  const restore = useMutation({
    mutationFn: api.restoreAccount,
    onSuccess: (data) => {
      queryClient.setQueryData(["me"], data);
      void queryClient.invalidateQueries();
    },
  });
  const p = profile.data;

  const signOut = (): void => {
    auth.clear();
    window.dispatchEvent(new Event("hg:signed-out"));
  };
  const togglePhenotype = (ph: Phenotype, on: boolean): void => {
    if (!p) return;
    const next = PHENOTYPES.filter((x) => (x === ph ? on : p.phenotypes.includes(x)));
    update.mutate({ phenotypes: next });
  };
  const toggleNotify = async (on: boolean): Promise<void> => {
    if (!on) {
      reminder.turnOff();
      setNotify(false);
      return;
    }
    const ok = await reminder.turnOn();
    setNotify(ok);
    setBlocked(!ok);
  };

  return (
    <div>
      <PageTitle title={t("settings.title")} />

      <Card>
        <div className="flex items-center gap-4">
          <span className="grid h-14 w-14 place-items-center rounded-full bg-brand text-xl font-bold text-white">{p?.display_name.slice(0, 1) ?? "?"}</span>
          <div>
            <p className="text-lg font-bold">{p?.display_name}</p>
            <p className="text-sm text-ink-soft">{p ? `${t(`today.dx_${p.diagnosis}`)} · ${t(`gut.kind_${p.state}`)}` : ""}</p>
          </div>
        </div>
      </Card>

      <SectionTitle>{t("settings.health_profile")}</SectionTitle>
      <Card>
        <p className="mb-2 text-[15px] font-semibold">{t("settings.diagnosis")}</p>
        <Segmented
          value={p?.diagnosis ?? null}
          onChange={(v) => update.mutate({ diagnosis: v })}
          options={[
            { value: "CD" as const, label: t("today.dx_CD") },
            { value: "UC" as const, label: t("today.dx_UC") },
          ]}
        />
        <p className="mb-2 mt-5 text-[15px] font-semibold">{t("settings.conditions")}</p>
        <div className="space-y-2">
          {PHENOTYPES.map((ph) => (
            <Toggle key={ph} label={t(`settings.ph_${ph}`)} checked={p?.phenotypes.includes(ph) ?? false} onChange={(on) => togglePhenotype(ph, on)} />
          ))}
        </div>
        <p className="mt-3 text-xs text-ink-faint">{t("settings.profile_note")}</p>
      </Card>

      <SectionTitle>{t("settings.preferences")}</SectionTitle>
      <Card className="space-y-5">
        <div className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-3 font-semibold">
            <Globe className="h-5 w-5 text-ink-faint" />
            {t("settings.language")}
          </span>
          <LangToggle />
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-3 font-semibold">
            <Bell className="h-5 w-5 text-ink-faint" />
            {t("settings.reminder")}
          </span>
          <input
            type="time"
            aria-label={t("settings.reminder")}
            className={`${inputClass} w-32`}
            value={p?.reminder_time ?? "22:30"}
            onChange={(e) => e.target.value && update.mutate({ reminder_time: e.target.value })}
          />
        </div>
        {reminder.supported() && <Toggle label={t("settings.notify")} checked={notify} onChange={(on) => void toggleNotify(on)} />}
        <p className="text-xs text-ink-faint">{blocked ? t("settings.notify_blocked") : t("settings.notify_note")}</p>
      </Card>

      <SectionTitle>{t("settings.safety")}</SectionTitle>
      <Card className="space-y-3 text-sm text-ink-soft">
        <p className="flex gap-3">
          <ShieldCheck className="h-5 w-5 shrink-0 text-brand" />
          {t("settings.safety_1")}
        </p>
        <p className="flex gap-3">
          <Stethoscope className="h-5 w-5 shrink-0 text-brand" />
          {t("settings.safety_2")}
        </p>
        <p className="rounded-xl bg-paper p-3 text-xs">{t("app.disclaimer")}</p>
      </Card>

      <SectionTitle>{t("settings.about")}</SectionTitle>
      <Card className="text-sm text-ink-soft">
        {health.data && (
          <dl className="space-y-1.5">
            <div className="flex justify-between gap-4">
              <dt>{t("settings.knowledge")}</dt>
              <dd className="text-right font-semibold text-ink">
                {t("settings.knowledge_value", { dishes: num(health.data.knowledge.dishes, lang), rules: num(health.data.knowledge.rule_cards, lang) })}
              </dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt>{t("settings.reviewed")}</dt>
              <dd className="text-right font-semibold text-ink">{t("settings.reviewed_value")}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt>{t("settings.photo_ai")}</dt>
              <dd className="text-right font-semibold text-ink">{health.data.models.perception ? t("settings.on") : t("settings.off")}</dd>
            </div>
          </dl>
        )}
        <p className="mt-3 border-t border-line pt-3 text-xs">{t("notice.purpose")}</p>
      </Card>

      {p?.is_synthetic && (
        <>
          <SectionTitle>{t("settings.account")}</SectionTitle>
          <Card>
            <p className="text-sm text-ink-soft">{t("settings.restore_note")}</p>
            <Button variant="secondary" className="mt-3 w-full" disabled={restore.isPending} onClick={() => restore.mutate()}>
              <RotateCcw className={restore.isPending ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
              {t("settings.restore")}
            </Button>
            {restore.isSuccess && <p className="mt-2 text-sm text-ok">{t("settings.restored")}</p>}
          </Card>
        </>
      )}

      <Button variant="outline" className="mt-6 w-full" onClick={signOut}>
        <LogOut className="h-4 w-4" />
        {t("settings.sign_out")}
      </Button>
    </div>
  );
}
