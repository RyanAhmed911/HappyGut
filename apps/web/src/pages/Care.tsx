import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, CalendarPlus, Pencil, Pill, Plus, ShieldCheck, Trash2, X } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { DoseList, useAppointments, useEvery, useMedications, useWhen } from "@/components/care";
import { LoadError, PageLoading, useLang } from "@/components/shell";
import { Button, Card, Chip, Empty, Field, inputClass, PageTitle, SectionTitle, Sheet, Toggle } from "@/components/ui";
import { api } from "@/lib/api";
import { clock, shortDate } from "@/lib/format";
import { keys } from "@/lib/hooks";
import { reminder, type CareKind } from "@/lib/reminder";
import { APPOINTMENT_KINDS, EVERY_DAYS, type Appointment, type Medication } from "@/lib/schemas";

function useRefresh(): () => void {
  const queryClient = useQueryClient();
  return () => {
    for (const key of [keys.medications, keys.appointments, ["diary"], ["report"]]) void queryClient.invalidateQueries({ queryKey: [...key] });
  };
}

function MedicineSheet({ open, onOpenChange, today, med }: { open: boolean; onOpenChange: (o: boolean) => void; today: string; med: Medication | null }) {
  const { t } = useTranslation();
  const refresh = useRefresh();
  const every = useEvery();
  const [name, setName] = useState(med?.name ?? "");
  const [times, setTimes] = useState<string[]>(med?.times ?? ["08:00"]);
  const [everyDays, setEveryDays] = useState(med?.every_days ?? 1);
  const [start, setStart] = useState(med?.start ?? today);
  const [note, setNote] = useState(med?.note ?? "");
  const [newTime, setNewTime] = useState("20:00");
  const save = useMutation({
    mutationFn: () => {
      const body = { name: name.trim(), times, every_days: everyDays, start, note: note.trim() };
      return med ? api.editMedication(med.id, body) : api.addMedication(body);
    },
    onSuccess: () => {
      refresh();
      onOpenChange(false);
    },
  });
  const addTime = (): void => {
    if (newTime && !times.includes(newTime) && times.length < 4) setTimes([...times, newTime].sort());
  };
  return (
    <Sheet open={open} onOpenChange={onOpenChange} title={med ? t("care.edit_medicine") : t("care.add_medicine")} description={t("care.medicine_hint")}>
      <Field label={t("care.medicine_name")}>
        <input className={inputClass} value={name} maxLength={60} onChange={(e) => setName(e.target.value)} placeholder={t("care.medicine_name_ph")} />
      </Field>
      <Field label={t("care.times")} hint={t("care.times_hint")}>
        <div className="flex flex-wrap items-center gap-1.5">
          {times.map((x) => (
            <span key={x} className="tabular inline-flex h-9 items-center gap-1 rounded-lg border border-brand/30 bg-brand-tint pl-3 pr-1 text-sm font-semibold text-brand-deep">
              {x}
              <button type="button" aria-label={t("app.remove")} disabled={times.length === 1} onClick={() => setTimes(times.filter((y) => y !== x))} className="rounded p-1 text-brand-deep/70 hover:bg-brand-soft disabled:opacity-30">
                <X className="h-3.5 w-3.5" />
              </button>
            </span>
          ))}
          {times.length < 4 && (
            <span className="inline-flex items-center gap-1">
              <input type="time" className={`${inputClass} h-9 w-28`} value={newTime} onChange={(e) => setNewTime(e.target.value)} aria-label={t("care.add_time")} />
              <Button size="sm" variant="secondary" className="whitespace-nowrap" onClick={addTime}>
                <Plus className="h-4 w-4" />
                {t("care.add_time")}
              </Button>
            </span>
          )}
        </div>
      </Field>
      <Field label={t("care.how_often")}>
        <div className="flex flex-wrap gap-1.5">
          {EVERY_DAYS.map((d) => (
            <Chip key={d} selected={everyDays === d} className="min-h-9 text-[13px]" onClick={() => setEveryDays(d)}>
              {every(d)}
            </Chip>
          ))}
        </div>
      </Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label={everyDays === 1 ? t("care.start") : t("care.next_due")}>
          <input type="date" className={inputClass} value={start} onChange={(e) => setStart(e.target.value)} />
        </Field>
        <Field label={t("care.note")}>
          <input className={inputClass} value={note} maxLength={80} onChange={(e) => setNote(e.target.value)} placeholder={t("care.note_ph")} />
        </Field>
      </div>
      {save.isError && <p className="mb-3 text-sm text-trigger">{t("care.save_error")}</p>}
      <Button className="w-full" disabled={!name.trim() || !times.length || !start || save.isPending} onClick={() => save.mutate()}>
        {t("app.save")}
      </Button>
    </Sheet>
  );
}

function AppointmentSheet({ open, onOpenChange, today }: { open: boolean; onOpenChange: (o: boolean) => void; today: string }) {
  const { t } = useTranslation();
  const refresh = useRefresh();
  const [kind, setKind] = useState<Appointment["kind"]>("blood_test");
  const [date, setDate] = useState(today);
  const [time, setTime] = useState("");
  const [note, setNote] = useState("");
  const add = useMutation({
    mutationFn: () => api.addAppointment({ kind, date, time: time || null, note: note.trim() }),
    onSuccess: () => {
      refresh();
      onOpenChange(false);
      setNote("");
    },
  });
  return (
    <Sheet open={open} onOpenChange={onOpenChange} title={t("care.add_test")} description={t("care.test_hint")}>
      <Field label={t("care.what")}>
        <div className="flex flex-wrap gap-1.5">
          {APPOINTMENT_KINDS.map((k) => (
            <Chip key={k} selected={kind === k} className="min-h-9 text-[13px]" onClick={() => setKind(k)}>
              {t(`care.kind_${k}`)}
            </Chip>
          ))}
        </div>
      </Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label={t("care.date")}>
          <input type="date" className={inputClass} value={date} onChange={(e) => setDate(e.target.value)} />
        </Field>
        <Field label={t("care.time_optional")}>
          <input type="time" className={inputClass} value={time} onChange={(e) => setTime(e.target.value)} />
        </Field>
      </div>
      <Field label={t("care.note")}>
        <input className={inputClass} value={note} maxLength={80} onChange={(e) => setNote(e.target.value)} placeholder={t("care.test_note_ph")} />
      </Field>
      {add.isError && <p className="mb-3 text-sm text-trigger">{t("care.save_error")}</p>}
      <Button className="w-full" disabled={!date || add.isPending} onClick={() => add.mutate()}>
        {t("app.save")}
      </Button>
    </Sheet>
  );
}

function ReminderToggles() {
  const { t } = useTranslation();
  const [on, setOn] = useState<Record<CareKind, boolean>>({ meds: reminder.careEnabled("meds"), tests: reminder.careEnabled("tests") });
  const [blocked, setBlocked] = useState(false);
  if (!reminder.supported()) return <p className="text-sm text-ink-soft">{t("care.reminders_unsupported")}</p>;
  const toggle = async (kind: CareKind, value: boolean): Promise<void> => {
    const ok = await reminder.setCare(kind, value);
    setOn((prev) => ({ ...prev, [kind]: ok }));
    setBlocked(value && !ok);
  };
  return (
    <div className="space-y-2">
      <Toggle label={t("care.remind_meds")} checked={on.meds} onChange={(v) => void toggle("meds", v)} />
      <Toggle label={t("care.remind_tests")} checked={on.tests} onChange={(v) => void toggle("tests", v)} />
      <p className="text-xs text-ink-faint">{blocked ? t("settings.notify_blocked") : t("care.reminders_note")}</p>
    </div>
  );
}

export function CarePage() {
  const { t } = useTranslation();
  const lang = useLang();
  const every = useEvery();
  const when = useWhen();
  const refresh = useRefresh();
  const meds = useMedications();
  const appts = useAppointments();
  const [editing, setEditing] = useState<Medication | null | "new">(null);
  const [addingTest, setAddingTest] = useState(false);
  const removeMed = useMutation({ mutationFn: (id: string) => api.deleteMedication(id), onSuccess: refresh });
  const removeTest = useMutation({ mutationFn: (id: string) => api.deleteAppointment(id), onSuccess: refresh });

  if (meds.isLoading || appts.isLoading) return <PageLoading />;
  if (meds.isError || appts.isError || !meds.data || !appts.data) {
    return <LoadError onRetry={() => { void meds.refetch(); void appts.refetch(); }} />;
  }
  const today = meds.data.today;
  const upcoming = appts.data.items.filter((a) => a.date >= today);
  const past = appts.data.items.filter((a) => a.date < today).reverse().slice(0, 5);

  return (
    <div>
      <PageTitle title={t("care.title")} subtitle={t("care.subtitle")} />

      <div className="lg:grid lg:grid-cols-12 lg:items-start lg:gap-x-6">
        <div className="lg:col-span-7">
          <SectionTitle>{t("care.doses_today")}</SectionTitle>
          <DoseList data={meds.data} />

          <SectionTitle
            action={
              <button type="button" className="text-sm font-semibold text-brand" onClick={() => setEditing("new")}>
                + {t("care.add_medicine")}
              </button>
            }
          >
            {t("care.my_medicines")}
          </SectionTitle>
          {meds.data.items.length ? (
            <Card className="divide-y divide-line p-0">
              {meds.data.items.map((m) => (
                <div key={m.id} className="flex items-center gap-3 px-4 py-3">
                  <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-brand-soft text-brand-deep">
                    <Pill className="h-4 w-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-semibold">{m.name}</p>
                    <p className="text-xs text-ink-faint">
                      {m.times.map((x) => clock(x, lang)).join(", ")} · {every(m.every_days)}
                      {m.every_days > 1 && ` · ${t("care.from_date", { date: shortDate(m.start, lang) })}`}
                      {m.note && ` · ${m.note}`}
                    </p>
                  </div>
                  <button type="button" aria-label={t("care.edit_medicine")} onClick={() => setEditing(m)} className="rounded-lg p-1.5 text-ink-faint hover:bg-paper-deep hover:text-ink">
                    <Pencil className="h-4 w-4" />
                  </button>
                  <button type="button" aria-label={t("app.remove")} disabled={removeMed.isPending} onClick={() => removeMed.mutate(m.id)} className="rounded-lg p-1.5 text-ink-faint hover:bg-paper-deep hover:text-trigger">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </Card>
          ) : (
            <Empty icon={<Pill className="h-8 w-8" />} title={t("care.no_medicines")}>
              <p>{t("care.no_medicines_text")}</p>
            </Empty>
          )}
        </div>

        <div className="lg:col-span-5">
          <SectionTitle
            action={
              <button type="button" className="text-sm font-semibold text-brand" onClick={() => setAddingTest(true)}>
                + {t("care.add_test")}
              </button>
            }
          >
            {t("care.tests")}
          </SectionTitle>
          {upcoming.length ? (
            <Card className="divide-y divide-line p-0">
              {upcoming.map((a) => (
                <div key={a.id} className="flex items-center gap-3 px-4 py-3">
                  <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-brand-soft text-brand-deep">
                    <CalendarPlus className="h-4 w-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-semibold">{t(`care.kind_${a.kind}`)}</p>
                    <p className="text-xs text-ink-faint">
                      {when(a.date, today)}
                      {a.time && ` · ${clock(a.time, lang)}`}
                      {a.note && ` · ${a.note}`}
                    </p>
                  </div>
                  <button type="button" aria-label={t("app.remove")} disabled={removeTest.isPending} onClick={() => removeTest.mutate(a.id)} className="rounded-lg p-1.5 text-ink-faint hover:bg-paper-deep hover:text-trigger">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </Card>
          ) : (
            <Empty icon={<CalendarPlus className="h-8 w-8" />} title={t("care.no_tests")}>
              <p>{t("care.no_tests_text")}</p>
            </Empty>
          )}
          {past.length > 0 && (
            <p className="mt-2 px-1 text-xs text-ink-faint">
              {t("care.past")}: {past.map((a) => `${t(`care.kind_${a.kind}`)} (${shortDate(a.date, lang)})`).join(" · ")}
            </p>
          )}

          <SectionTitle>
            <span className="inline-flex items-center gap-1.5">
              <Bell className="h-3.5 w-3.5" />
              {t("care.reminders")}
            </span>
          </SectionTitle>
          <ReminderToggles />
        </div>
      </div>

      <p className="mt-8 flex gap-2.5 rounded-2xl bg-paper-deep/70 p-4 text-sm text-ink-soft">
        <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
        <span>{t("care.safety")}</span>
      </p>

      {editing !== null && (
        <MedicineSheet
          key={editing === "new" ? "new" : editing.id}
          open
          onOpenChange={(o) => !o && setEditing(null)}
          today={today}
          med={editing === "new" ? null : editing}
        />
      )}
      <AppointmentSheet key={String(addingTest)} open={addingTest} onOpenChange={setAddingTest} today={today} />
    </div>
  );
}
