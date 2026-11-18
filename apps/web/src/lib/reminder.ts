import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { api } from "./api";

const ENABLED = "hg.reminder.enabled";
const LAST = "hg.reminder.last";
/** Medicine and test reminders have their own switches; the permission is shared with the diary reminder. */
export type CareKind = "meds" | "tests";
const CARE_KEY: Record<CareKind, string> = { meds: "hg.reminder.meds", tests: "hg.reminder.tests" };
const SHOWN = "hg.reminder.shown"; // ids of care reminders already shown (kept for a few days)

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
  careEnabled: (kind: CareKind): boolean =>
    reminder.supported() && localStorage.getItem(CARE_KEY[kind]) === "1" && Notification.permission === "granted",
  /** Turn a medicine or test reminder on (asks for permission from a tap) or off. */
  async setCare(kind: CareKind, on: boolean): Promise<boolean> {
    if (!on) {
      localStorage.setItem(CARE_KEY[kind], "0");
      return false;
    }
    if (!reminder.supported()) return false;
    const permission = Notification.permission === "default" ? await Notification.requestPermission() : Notification.permission;
    const ok = permission === "granted";
    localStorage.setItem(CARE_KEY[kind], ok ? "1" : "0");
    return ok;
  },
};

async function notify(title: string, body: string, tag: string, url: string): Promise<void> {
  const options = { body, icon: "/icon-192.png", badge: "/icon-192.png", tag, data: { url } };
  const registration = await navigator.serviceWorker?.getRegistration();
  if (registration) await registration.showNotification(title, options);
  else new Notification(title, options);
}

function shownIds(): string[] {
  try {
    return JSON.parse(localStorage.getItem(SHOWN) ?? "[]") as string[];
  } catch {
    return [];
  }
}

/** Remember a shown reminder; returns false if it was already shown. */
function markShown(id: string): boolean {
  const ids = shownIds();
  if (ids.includes(id)) return false;
  localStorage.setItem(SHOWN, JSON.stringify([...ids, id].slice(-200)));
  return true;
}

/** A dose reminder is due from its time until an hour after it, if the dose isn't ticked yet. */
export function doseDue(nowMinutes: number, time: string, taken: boolean): boolean {
  const at = minutesOf(time);
  return !taken && nowMinutes >= at && nowMinutes < at + 60;
}

/** Test reminders: the evening before (from 20:00) and the morning of the day (from 07:30). */
export function testStage(now: Date, today: string, tomorrow: string, date: string): "eve" | "day" | null {
  const minutes = now.getHours() * 60 + now.getMinutes();
  if (date === tomorrow && minutes >= 20 * 60) return "eve";
  if (date === today && minutes >= 7 * 60 + 30) return "day";
  return null;
}

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

/**
 * Medicine and test reminders while HappyGut is open or installed and running. They only repeat the
 * schedule the patient entered; they never advise on a medicine. (Server push for a closed app is a later step.)
 */
export function useCareReminders(): void {
  const { t } = useTranslation();
  useEffect(() => {
    const check = async (): Promise<void> => {
      const meds = reminder.careEnabled("meds");
      const tests = reminder.careEnabled("tests");
      if (!meds && !tests) return;
      try {
        const now = new Date();
        const minutes = now.getHours() * 60 + now.getMinutes();
        if (meds) {
          const m = await api.medications();
          for (const d of m.day.doses) {
            if (doseDue(minutes, d.time, d.taken) && markShown(`dose:${m.day.date}:${d.medication_id}:${d.time}`)) {
              await notify(t("care.notify_dose_title"), t("care.notify_dose_body", { name: d.name, time: d.time }), `hg-dose-${d.medication_id}`, "/care");
            }
          }
        }
        if (tests) {
          const a = await api.appointments();
          const tomorrow = new Date(`${a.today}T12:00:00`);
          tomorrow.setDate(tomorrow.getDate() + 1);
          const tomorrowIso = `${tomorrow.getFullYear()}-${String(tomorrow.getMonth() + 1).padStart(2, "0")}-${String(tomorrow.getDate()).padStart(2, "0")}`;
          for (const item of a.items) {
            const stage = testStage(now, a.today, tomorrowIso, item.date);
            if (stage && markShown(`test:${item.id}:${stage}`)) {
              const what = t(`care.kind_${item.kind}`);
              const body = item.time ? t(`care.notify_test_${stage}_at`, { what, time: item.time }) : t(`care.notify_test_${stage}`, { what });
              await notify(t("care.notify_test_title"), body, `hg-test-${item.id}`, "/care");
            }
          }
        }
      } catch {
        /* offline or signed out: try again on the next tick */
      }
    };
    void check();
    const id = window.setInterval(() => void check(), 60_000);
    return () => window.clearInterval(id);
  }, [t]);
}
