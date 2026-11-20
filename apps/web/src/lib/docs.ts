/** API client for the live /docs page. The admin token is separate from the patient sign-in and lives only for the tab. */
import { z } from "zod";

const BASE: string = (import.meta.env.VITE_API_URL as string | undefined) ?? "/api";
const ADMIN_KEY = "hg.docsAdmin";

const Bilingual = z.object({ en: z.string(), bn: z.string() });
const Member = z.object({ name: z.string(), role: z.string(), email: z.string(), photo_url: z.string() });
const Team = z.object({ name: z.string(), members: z.array(Member) });
const Order = z.object({ pitch: z.array(z.string()), tech: z.array(z.string()) });
const Window = z.object({ visible: z.boolean(), starts_at: z.string().nullable(), ends_at: z.string().nullable() });
const Reason = z.enum(["open", "off", "not_yet", "ended"]);
const Arm = z.object({ roc_auc: z.number(), average_precision: z.number(), top_10_percent: z.object({ caught: z.number(), of: z.number() }) });

export const DocsLive = z.object({
  served_at: z.string(),
  started_at: z.string(),
  uptime_s: z.number(),
  version: z.string(),
  engine_version: z.string(),
  timezone: z.string(),
  knowledge: z.object({ dishes: z.number(), rule_cards: z.number() }).passthrough(),
  models: z.object({ perception: z.boolean(), explanation: z.boolean() }),
  model_names: z.record(z.string(), z.array(z.string())),
  tracing: z.boolean(),
  storage: z.string(),
  demo_mode: z.boolean(),
  accounts: z.array(z.object({ email: z.string(), role: z.string() })),
  usage: z.record(z.string(), z.number()).nullable(),
  flare_model: z
    .object({ version: z.string().nullable(), trained: z.string().nullable(), base_rate: z.number().nullable(), features: z.number(), v1: Arm, v0: Arm })
    .nullable(),
  features: z.array(z.object({ id: z.string(), status: z.enum(["live", "off", "template", "built", "planned"]) })),
  endpoints: z.array(z.object({ method: z.string(), path: z.string(), access: z.enum(["public", "patient", "job_token", "docs_admin"]), summary: z.string() })),
});
export type DocsLive = z.infer<typeof DocsLive>;

export const DocsPage = Window.extend({
  available: z.boolean(),
  reason: Reason,
  preview: z.boolean(),
  sections: z.record(z.string(), Bilingual),
  order: Order,
  team: Team,
  updated_at: z.string().nullable(),
  live: DocsLive,
});
export type DocsPage = z.infer<typeof DocsPage>;

export const DocsStatus = Window.extend({ available: z.boolean(), reason: Reason, admin: z.boolean() });
export type DocsStatus = z.infer<typeof DocsStatus>;

export const DocsAdminState = Window.extend({
  available: z.boolean(),
  reason: Reason,
  sections: z.record(z.string(), Bilingual),
  order: Order,
  team: Team,
  updated_at: z.string().nullable(),
  history: z.array(z.object({ at: z.string(), change: z.string() })),
});
export type DocsAdminState = z.infer<typeof DocsAdminState>;
export type TeamMember = z.infer<typeof Member>;

export class DocsError extends Error {
  constructor(
    public status: number,
    public code: string,
  ) {
    super(`${status} ${code}`);
  }
}

export const docsAdmin = {
  get token(): string | null {
    try {
      return sessionStorage.getItem(ADMIN_KEY);
    } catch {
      return null;
    }
  },
  set(token: string): void {
    try {
      sessionStorage.setItem(ADMIN_KEY, token);
    } catch {
      /* private mode: the token lasts for this page only */
    }
  },
  clear(): void {
    try {
      sessionStorage.removeItem(ADMIN_KEY);
    } catch {
      /* nothing stored */
    }
  },
};

async function call<T extends z.ZodType>(schema: T, path: string, init: RequestInit = {}, admin = false): Promise<z.infer<T>> {
  const headers = new Headers(init.headers);
  const token = docsAdmin.token;
  if (token && (admin || path === "/v1/docs")) headers.set("Authorization", `Bearer ${token}`);
  if (typeof init.body === "string") headers.set("Content-Type", "application/json");
  const response = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!response.ok) {
    let code = response.statusText;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") code = body.detail;
    } catch {
      /* not JSON */
    }
    if (response.status === 401 && admin) docsAdmin.clear();
    throw new DocsError(response.status, code);
  }
  return schema.parse(await response.json());
}

const put = (body: unknown): RequestInit => ({ method: "PUT", body: JSON.stringify(body) });

export const docsApi = {
  page: () => call(DocsPage, "/v1/docs"),
  status: () => call(DocsStatus, "/v1/docs/status"),
  async login(password: string): Promise<void> {
    const body = await call(z.object({ token: z.string() }), "/v1/docs/admin/login", { method: "POST", body: JSON.stringify({ password }) });
    docsAdmin.set(body.token);
  },
  state: () => call(DocsAdminState, "/v1/docs/admin", {}, true),
  settings: (body: { visible: boolean; starts_at: string | null; ends_at: string | null }) =>
    call(DocsAdminState, "/v1/docs/admin/settings", put(body), true),
  section: (id: string, body: { en: string; bn: string }) => call(DocsAdminState, `/v1/docs/admin/sections/${id}`, put(body), true),
  resetSection: (id: string) => call(DocsAdminState, `/v1/docs/admin/sections/${id}`, { method: "DELETE" }, true),
  order: (body: { pitch: string[]; tech: string[] }) => call(DocsAdminState, "/v1/docs/admin/order", put(body), true),
  team: (body: { team_name: string; members: TeamMember[] }) => call(DocsAdminState, "/v1/docs/admin/team", put(body), true),
};
