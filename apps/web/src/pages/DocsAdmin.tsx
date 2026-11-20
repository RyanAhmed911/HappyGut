import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, Download, ExternalLink, KeyRound, LogOut, Plus, Trash2 } from "lucide-react";
import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { LangToggle, Logo, useLang } from "@/components/shell";
import { Badge, Button, Card, Field, Skeleton, Toggle, inputClass } from "@/components/ui";
import { SECTIONS, sectionText, type DocLang } from "@/data/docsContent";
import { cn } from "@/lib/cn";
import { DocsError, docsAdmin, docsApi, type DocsAdminState, type TeamMember } from "@/lib/docs";
import { dhakaTime } from "./Docs";

const KEY = ["docsAdmin"] as const;
const DHAKA_OFFSET = "+06:00"; // Bangladesh has no daylight saving time

/** ISO timestamp → the value of a datetime-local input, in Dhaka time. */
function toLocalInput(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(new Date(iso).getTime() + 6 * 3600_000);
  return d.toISOString().slice(0, 16);
}

const fromLocalInput = (value: string): string | null => (value ? `${value}:00${DHAKA_OFFSET}` : null);

function Panel({ title, children, hint }: { title: string; hint?: string; children: ReactNode }) {
  return (
    <Card className="p-5">
      <h2 className="text-lg font-bold">{title}</h2>
      {hint && <p className="mt-0.5 text-sm text-ink-faint">{hint}</p>}
      <div className="mt-4">{children}</div>
    </Card>
  );
}

function Login({ onDone }: { onDone: () => void }) {
  const { t } = useTranslation();
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const submit = async (e: FormEvent): Promise<void> => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await docsApi.login(password);
      onDone();
    } catch (err) {
      const code = err instanceof DocsError ? err.code : "error";
      setError(["invalid_credentials", "too_many_attempts", "docs_admin_disabled"].includes(code) ? t(`docs_admin.err_${code}`) : t("app.error"));
    } finally {
      setBusy(false);
    }
  };
  return (
    <Card className="mx-auto mt-10 max-w-sm p-6">
      <span className="grid h-11 w-11 place-items-center rounded-full bg-brand-soft text-brand-deep">
        <KeyRound className="h-5 w-5" />
      </span>
      <h1 className="mt-4 text-xl font-bold">{t("docs_admin.login_title")}</h1>
      <p className="mt-1 text-sm text-ink-soft">{t("docs_admin.login_hint")}</p>
      <form onSubmit={(e) => void submit(e)} className="mt-5 space-y-3">
        <Field label={t("docs_admin.password")}>
          <input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} className={inputClass} required />
        </Field>
        {error && <p role="alert" className="text-sm font-semibold text-trigger">{error}</p>}
        <Button type="submit" className="w-full" disabled={busy || !password}>
          {t("docs_admin.sign_in")}
        </Button>
      </form>
    </Card>
  );
}

function Visibility({ state, save }: { state: DocsAdminState; save: (fn: () => Promise<DocsAdminState>) => Promise<void> }) {
  const { t } = useTranslation();
  const lang = useLang();
  const [visible, setVisible] = useState(state.visible);
  const [start, setStart] = useState(toLocalInput(state.starts_at));
  const [end, setEnd] = useState(toLocalInput(state.ends_at));
  useEffect(() => {
    setVisible(state.visible);
    setStart(toLocalInput(state.starts_at));
    setEnd(toLocalInput(state.ends_at));
  }, [state.visible, state.starts_at, state.ends_at]);
  const tone = state.available ? "brand" : "trigger";
  return (
    <Panel title={t("docs_admin.visibility")} hint={t("docs_admin.visibility_hint")}>
      <p className="mb-3 flex flex-wrap items-center gap-2 text-sm">
        <Badge tone={tone}>{t(`docs_admin.reason_${state.reason}`)}</Badge>
        {(state.starts_at || state.ends_at) && (
          <span className="text-ink-soft">
            {state.starts_at ? dhakaTime(state.starts_at, lang) : "…"} – {state.ends_at ? dhakaTime(state.ends_at, lang) : "…"}
          </span>
        )}
      </p>
      <Toggle checked={visible} onChange={setVisible} label={t("docs_admin.visible")} />
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <Field label={t("docs_admin.starts_at")}>
          <input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} className={inputClass} />
        </Field>
        <Field label={t("docs_admin.ends_at")}>
          <input type="datetime-local" value={end} onChange={(e) => setEnd(e.target.value)} className={inputClass} />
        </Field>
      </div>
      <p className="mt-2 text-xs text-ink-faint">{t("docs_admin.window_hint")}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button onClick={() => void save(() => docsApi.settings({ visible, starts_at: fromLocalInput(start), ends_at: fromLocalInput(end) }))}>{t("app.save")}</Button>
        <Button
          variant="outline"
          onClick={() => {
            setStart("");
            setEnd("");
            void save(() => docsApi.settings({ visible, starts_at: null, ends_at: null }));
          }}
        >
          {t("docs_admin.clear_window")}
        </Button>
      </div>
    </Panel>
  );
}

function SectionEditor({ state, save }: { state: DocsAdminState; save: (fn: () => Promise<DocsAdminState>) => Promise<void> }) {
  const { t } = useTranslation();
  const lang = useLang();
  const [id, setId] = useState(SECTIONS[0]!.id);
  const section = SECTIONS.find((s) => s.id === id)!;
  const override = state.sections[id];
  const [text, setText] = useState({ en: "", bn: "" });
  useEffect(() => {
    setText(override ?? { en: sectionText(section, "en"), bn: sectionText(section, "bn") });
  }, [id, override, section]);
  const area = cn(inputClass, "h-auto min-h-40 py-2.5 leading-relaxed");
  return (
    <Panel title={t("docs_admin.sections")} hint={t("docs_admin.sections_hint")}>
      <Field label={t("docs_admin.section")}>
        <select value={id} onChange={(e) => setId(e.target.value)} className={inputClass}>
          {(["pitch", "tech"] as const).map((part) => (
            <optgroup key={part} label={t(`docs.part_${part}`)}>
              {SECTIONS.filter((s) => s.part === part).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.title[lang as DocLang]}
                  {state.sections[s.id] ? " ✎" : ""}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </Field>
      <div className="mt-3 grid gap-3 lg:grid-cols-2">
        <Field label="English">
          <textarea value={text.en} onChange={(e) => setText({ ...text, en: e.target.value })} className={area} maxLength={4000} />
        </Field>
        <Field label="বাংলা">
          <textarea value={text.bn} onChange={(e) => setText({ ...text, bn: e.target.value })} className={area} maxLength={4000} />
        </Field>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button disabled={!text.en.trim() || !text.bn.trim()} onClick={() => void save(() => docsApi.section(id, text))}>
          {t("app.save")}
        </Button>
        {override && (
          <Button variant="outline" onClick={() => void save(() => docsApi.resetSection(id))}>
            {t("docs_admin.reset_section")}
          </Button>
        )}
      </div>
    </Panel>
  );
}

function OrderEditor({ state, save }: { state: DocsAdminState; save: (fn: () => Promise<DocsAdminState>) => Promise<void> }) {
  const { t } = useTranslation();
  const lang = useLang() as DocLang;
  const [order, setOrder] = useState(state.order);
  useEffect(() => setOrder(state.order), [state.order]);
  const title = (id: string): string => SECTIONS.find((s) => s.id === id)?.title[lang] ?? id;
  const move = (part: "pitch" | "tech", i: number, by: -1 | 1): void => {
    const list = [...order[part]];
    const j = i + by;
    if (j < 0 || j >= list.length) return;
    [list[i], list[j]] = [list[j]!, list[i]!];
    setOrder({ ...order, [part]: list });
  };
  return (
    <Panel title={t("docs_admin.order")} hint={t("docs_admin.order_hint")}>
      <div className="grid gap-4 lg:grid-cols-2">
        {(["pitch", "tech"] as const).map((part) => (
          <div key={part}>
            <p className="mb-2 text-xs font-bold uppercase tracking-wider text-ink-faint">{t(`docs.part_${part}`)}</p>
            <ol className="space-y-1">
              {order[part].map((id, i) => (
                <li key={id} className="flex items-center gap-2 rounded-lg border border-line bg-card px-2.5 py-1.5 text-sm">
                  <span className="tabular w-5 text-ink-faint">{i + 1}</span>
                  <span className="flex-1">{title(id)}</span>
                  <button type="button" onClick={() => move(part, i, -1)} disabled={i === 0} className="rounded p-1 hover:bg-paper-deep disabled:opacity-30" aria-label={t("docs_admin.move_up")}>
                    <ChevronUp className="h-4 w-4" />
                  </button>
                  <button type="button" onClick={() => move(part, i, 1)} disabled={i === order[part].length - 1} className="rounded p-1 hover:bg-paper-deep disabled:opacity-30" aria-label={t("docs_admin.move_down")}>
                    <ChevronDown className="h-4 w-4" />
                  </button>
                </li>
              ))}
            </ol>
          </div>
        ))}
      </div>
      <Button className="mt-4" onClick={() => void save(() => docsApi.order(order))}>
        {t("app.save")}
      </Button>
    </Panel>
  );
}

function TeamEditor({ state, save }: { state: DocsAdminState; save: (fn: () => Promise<DocsAdminState>) => Promise<void> }) {
  const { t } = useTranslation();
  const [name, setName] = useState(state.team.name);
  const [members, setMembers] = useState<TeamMember[]>(state.team.members);
  useEffect(() => {
    setName(state.team.name);
    setMembers(state.team.members);
  }, [state.team]);
  const update = (i: number, patch: Partial<TeamMember>): void => setMembers(members.map((m, j) => (j === i ? { ...m, ...patch } : m)));
  return (
    <Panel title={t("docs_admin.team")} hint={t("docs_admin.team_hint")}>
      <Field label={t("docs_admin.team_name")}>
        <input value={name} onChange={(e) => setName(e.target.value)} className={inputClass} maxLength={80} />
      </Field>
      <ul className="mt-3 space-y-3">
        {members.map((m, i) => (
          <li key={i} className="grid gap-2 rounded-xl border border-line p-3 sm:grid-cols-2">
            <input value={m.name} onChange={(e) => update(i, { name: e.target.value })} placeholder={t("docs_admin.member_name")} aria-label={t("docs_admin.member_name")} className={inputClass} maxLength={80} />
            <input value={m.role} onChange={(e) => update(i, { role: e.target.value })} placeholder={t("docs_admin.member_role")} aria-label={t("docs_admin.member_role")} className={inputClass} maxLength={80} />
            <input type="email" value={m.email} onChange={(e) => update(i, { email: e.target.value })} placeholder={t("docs_admin.member_email")} aria-label={t("docs_admin.member_email")} className={inputClass} maxLength={120} />
            <div className="flex gap-2">
              <input type="url" value={m.photo_url} onChange={(e) => update(i, { photo_url: e.target.value })} placeholder={t("docs_admin.member_photo")} aria-label={t("docs_admin.member_photo")} className={inputClass} maxLength={500} />
              <button type="button" onClick={() => setMembers(members.filter((_, j) => j !== i))} disabled={members.length === 1} className="shrink-0 rounded-lg border border-line px-2.5 text-ink-faint hover:text-trigger disabled:opacity-30" aria-label={t("app.remove")}>
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </li>
        ))}
      </ul>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button variant="outline" disabled={members.length >= 12} onClick={() => setMembers([...members, { name: "", role: "", email: "", photo_url: "" }])}>
          <Plus className="h-4 w-4" /> {t("docs_admin.add_member")}
        </Button>
        <Button disabled={members.some((m) => !m.name.trim())} onClick={() => void save(() => docsApi.team({ team_name: name, members }))}>
          {t("app.save")}
        </Button>
      </div>
    </Panel>
  );
}

export function DocsAdmin() {
  const { t } = useTranslation();
  const lang = useLang();
  const queryClient = useQueryClient();
  const [signedIn, setSignedIn] = useState(Boolean(docsAdmin.token));
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const state = useQuery({ queryKey: KEY, queryFn: docsApi.state, enabled: signedIn, retry: false });

  useEffect(() => {
    if (state.error instanceof DocsError && state.error.status === 401) setSignedIn(false);
  }, [state.error]);

  const save = async (fn: () => Promise<DocsAdminState>): Promise<void> => {
    setMessage(null);
    try {
      queryClient.setQueryData(KEY, await fn());
      void queryClient.invalidateQueries({ queryKey: ["docsPage"] });
      setMessage({ ok: true, text: t("docs_admin.saved") });
    } catch (err) {
      if (err instanceof DocsError && err.status === 401) setSignedIn(false);
      setMessage({ ok: false, text: err instanceof DocsError && err.status === 422 ? t("docs_admin.err_invalid") : t("app.error") });
    }
  };

  const signOut = (): void => {
    docsAdmin.clear();
    queryClient.removeQueries({ queryKey: KEY });
    setSignedIn(false);
  };

  const exportJson = (): void => {
    if (!state.data) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(state.data, null, 2)], { type: "application/json" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "happygut-docs-settings.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-dvh">
      <header className="sticky top-0 z-20 border-b border-line bg-paper/85 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between gap-2 px-4">
          <Link to="/docs" className="flex items-center gap-2">
            <Logo className="[&>span]:text-lg" />
            <span className="rounded-md bg-saffron-soft px-1.5 py-0.5 text-xs font-bold text-caution">{t("docs_admin.badge")}</span>
          </Link>
          <div className="flex items-center gap-1.5">
            {signedIn && (
              <button type="button" onClick={signOut} className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-line bg-card px-2.5 text-[13px] font-semibold">
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">{t("docs_admin.sign_out")}</span>
              </button>
            )}
            <LangToggle />
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 pb-20 pt-6">
        {!signedIn ? (
          <Login onDone={() => setSignedIn(true)} />
        ) : !state.data ? (
          <div className="space-y-3">
            <Skeleton className="h-48" />
            <Skeleton className="h-48" />
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <h1 className="text-2xl font-bold">{t("docs_admin.title")}</h1>
                <p className="mt-1 text-sm text-ink-soft">{t("docs_admin.subtitle")}</p>
              </div>
              <div className="flex gap-2">
                <a href="/docs" target="_blank" rel="noreferrer" className="inline-flex h-10 items-center gap-1.5 rounded-lg border border-line bg-card px-3 text-sm font-semibold">
                  <ExternalLink className="h-4 w-4" /> {t("docs_admin.open_page")}
                </a>
                <Button variant="outline" onClick={exportJson}>
                  <Download className="h-4 w-4" /> {t("docs_admin.export")}
                </Button>
              </div>
            </div>
            {message && (
              <p role="status" className={cn("rounded-lg px-3 py-2 text-sm font-semibold", message.ok ? "bg-brand-soft text-brand-deep" : "bg-trigger-soft text-trigger")}>
                {message.text}
              </p>
            )}
            <Visibility state={state.data} save={save} />
            <TeamEditor state={state.data} save={save} />
            <SectionEditor state={state.data} save={save} />
            <OrderEditor state={state.data} save={save} />
            <Panel title={t("docs_admin.history")} hint={t("docs_admin.history_hint")}>
              {state.data.history.length === 0 ? (
                <p className="text-sm text-ink-faint">{t("docs_admin.history_empty")}</p>
              ) : (
                <ul className="space-y-1.5 text-sm">
                  {state.data.history.map((h) => (
                    <li key={h.at + h.change} className="flex flex-wrap gap-x-3">
                      <span className="tabular text-ink-faint">{dhakaTime(h.at, lang)}</span>
                      <span>{h.change}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>
          </div>
        )}
      </main>
    </div>
  );
}
