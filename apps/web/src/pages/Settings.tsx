import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, Globe, LogOut, ShieldCheck, Stethoscope } from "lucide-react";
import { useTranslation } from "react-i18next";
import { LangToggle, useLang, useProfile } from "@/components/shell";
import { Badge, Button, Card, inputClass, PageTitle, SectionTitle } from "@/components/ui";
import { api, auth } from "@/lib/api";
import { num } from "@/lib/format";

export function SettingsPage() {
  const { t } = useTranslation();
  const lang = useLang();
  const queryClient = useQueryClient();
  const profile = useProfile();
  const health = useQuery({ queryKey: ["health"], queryFn: api.health });
  const update = useMutation({
    mutationFn: (reminder_time: string) => api.updateMe({ reminder_time }),
    onSuccess: (data) => queryClient.setQueryData(["me"], data),
  });
  const p = profile.data;

  const signOut = (): void => {
    auth.clear();
    window.dispatchEvent(new Event("hg:signed-out"));
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
            {p?.is_synthetic && (
              <Badge tone="saffron" className="mt-1">
                {t("app.simulated_long")}
              </Badge>
            )}
          </div>
        </div>
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
            <span>
              {t("settings.reminder")}
              <span className="block text-xs font-normal text-ink-faint">{t("settings.reminder_note")}</span>
            </span>
          </span>
          <input
            type="time"
            aria-label={t("settings.reminder")}
            className={`${inputClass} w-32`}
            value={p?.reminder_time ?? "22:30"}
            onChange={(e) => e.target.value && update.mutate(e.target.value)}
          />
        </div>
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
        <p className="rounded-2xl bg-paper p-3 text-xs">{t("app.disclaimer")}</p>
      </Card>

      <SectionTitle>{t("settings.about")}</SectionTitle>
      <Card className="text-sm text-ink-soft">
        {health.data && (
          <dl className="space-y-1.5">
            <div className="flex justify-between">
              <dt>{t("settings.knowledge")}</dt>
              <dd className="font-semibold text-ink">
                {t("settings.knowledge_value", { dishes: num(health.data.knowledge.dishes, lang), rules: num(health.data.knowledge.rule_cards, lang) })}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt>{t("settings.reviewed")}</dt>
              <dd className="font-semibold text-ink">{health.data.knowledge.reviewed_only ? t("app.yes") : t("settings.reviewed_no")}</dd>
            </div>
            <div className="flex justify-between">
              <dt>{t("settings.photo_ai")}</dt>
              <dd className="font-semibold text-ink">{health.data.models.perception ? t("settings.on") : t("settings.off")}</dd>
            </div>
          </dl>
        )}
      </Card>

      <Button variant="outline" className="mt-6 w-full" onClick={signOut}>
        <LogOut className="h-4 w-4" />
        {t("settings.sign_out")}
      </Button>
    </div>
  );
}
