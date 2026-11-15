import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { api } from "./api";

const ENABLED = "hg.reminder.enabled";
const LAST = "hg.reminder.last";

export const reminder = {
  supported: (): boolean => typeof window !== "undefined" && "Notification" in window,
  enabled: (): boolean => reminder.supported() && localStorage.getItem(ENABLED) === "1" && Notification.permission === "granted",
  /** Ask for permission (must be called from a tap). Returns whether reminders are now on. */
  async turnOn(): Promise<boolean> {
    if (!reminder.supported()) return false;
    const permission = Notification.permission === "default" ? await Notification.requestPermission() : Notification.permission;
    const ok = permission === "granted";
    localStorage.setItem(ENABLED, ok ? "1" : "0");
    return ok;
  },
  turnOff(): void {
    localStorage.setItem(ENABLED, "0");
  },
};

/** Minutes since midnight for "HH:MM". */
export function minutesOf(hhmm: string): number {
  const [h, m] = hhmm.split(":").map(Number);
  return (h ?? 0) * 60 + (m ?? 0);
}

/** True when a reminder is due: it is at or past the reminder time and none was shown today. */
export function isDue(now: Date, reminderTime: string, lastShownDay: string | null, today: string): boolean {
  return now.getHours() * 60 + now.getMinutes() >= minutesOf(reminderTime) && lastShownDay !== today;
}

/**
 * Diary reminder while HappyGut is open or installed and running: at the chosen time, if tonight's
 * diary isn't filled in, show one notification. (Server push for a closed app is a later step.)
 */
export function useDiaryReminder(reminderTime: string | undefined): void {
  const { t } = useTranslation();
  useEffect(() => {
    if (!reminderTime) return;
    const check = async (): Promise<void> => {
      if (!reminder.enabled()) return;
      try {
        const today = (await api.days(1)).today;
        if (!isDue(new Date(), reminderTime, localStorage.getItem(LAST), today)) return;
        localStorage.setItem(LAST, today);
        if ((await api.diary(today)).entry) return; // already filled in
        const options = { body: t("reminder.body"), icon: "/icon-192.png", badge: "/icon-192.png", tag: "hg-diary", data: { url: "/diary" } };
        const registration = await navigator.serviceWorker?.getRegistration();
        if (registration) await registration.showNotification(t("reminder.title"), options);
        else new Notification(t("reminder.title"), options);
      } catch {
        /* offline or signed out: try again on the next tick */
      }
    };
    void check();
    const id = window.setInterval(() => void check(), 60_000);
    return () => window.clearInterval(id);
  }, [reminderTime, t]);
}
