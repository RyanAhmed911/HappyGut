import type { z } from "zod";
import * as S from "./schemas";
import { readSse, type SseEvent } from "./sse";

const BASE: string = (import.meta.env.VITE_API_URL as string | undefined) ?? "/api";
const TOKEN_KEY = "hg.token";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
  ) {
    super(`${status} ${code}`);
  }
}

export const auth = {
  get token(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },
  set(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
  },
  clear(): void {
    localStorage.removeItem(TOKEN_KEY);
  },
};

async function raw(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  if (auth.token) headers.set("Authorization", `Bearer ${auth.token}`);
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
    if (response.status === 401 && auth.token) {
      auth.clear();
      window.dispatchEvent(new Event("hg:signed-out"));
    }
    throw new ApiError(response.status, code);
  }
  return response;
}

async function json<T extends z.ZodType>(schema: T, path: string, init?: RequestInit): Promise<z.infer<T>> {
  const response = await raw(path, init);
  return schema.parse(await response.json());
}

const send = (method: string, body?: unknown): RequestInit => ({ method, body: body === undefined ? undefined : JSON.stringify(body) });

export const api = {
  health: () => json(S.Health, "/v1/health"),
  async login(email: string, password: string): Promise<void> {
    const response = await raw("/v1/auth/login", send("POST", { email, password }));
    auth.set(((await response.json()) as { token: string }).token);
  },
  restoreAccount: () => json(S.Profile, "/v1/account/restore", { method: "POST" }),
  me: () => json(S.Profile, "/v1/me"),
  updateMe: (body: { language?: "bn" | "en"; reminder_time?: string; diagnosis?: "CD" | "UC"; phenotypes?: S.Phenotype[] }) =>
    json(S.Profile, "/v1/me", send("PATCH", body)),
  foodGuide: async () => (await json(S.Guide, "/v1/foods/guide")).items,
  mealPlan: () => json(S.MealPlan, "/v1/foods/plan"),

  async mealCheck(form: FormData, onEvent: (e: SseEvent) => void, signal?: AbortSignal): Promise<void> {
    const response = await raw("/v1/meal-checks", { method: "POST", body: form, signal });
    await readSse(response, onEvent);
  },
  mealChecks: async (limit = 30) => (await json(S.MealCheckList, `/v1/meal-checks?limit=${limit}`)).items,
  mealCheckById: (id: string) => json(S.MealCheck, `/v1/meal-checks/${id}`),
  feedback: (id: string, answer: "right" | "wrong" | "not_sure") => raw(`/v1/meal-checks/${id}/feedback`, send("POST", { answer })),

  diary: (date: string) => json(S.DiaryDay, `/v1/diary/${date}`),
  saveDiary: (date: string, body: S.DiaryBody, lang: string) => json(S.DiarySaved, `/v1/diary/${date}?lang=${lang}`, send("PUT", body)),
  days: (limit = 180) => json(S.Days, `/v1/diary/days?limit=${limit}`),

  stressPeriods: async () => (await json(S.StressPeriodList, "/v1/stress-periods")).items,
  addStressPeriod: (body: Omit<S.StressPeriod, "id">) => json(S.StressPeriod, "/v1/stress-periods", send("POST", body)),
  deleteStressPeriod: (id: string) => raw(`/v1/stress-periods/${id}`, { method: "DELETE" }),

  patterns: (scope: string) => json(S.Patterns, `/v1/insights/patterns?scope=${scope}`),
  periods: () => json(S.Periods, "/v1/insights/periods"),
  decidePeriod: (start: string, decision: "confirm" | "reject") =>
    json(S.Periods, "/v1/insights/periods/decision", send("POST", { start, decision })),
  addFlare: (start: string, end: string | null) => json(S.Periods, "/v1/insights/periods/manual", send("POST", { start, end })),
  risk: () => json(S.Risk, "/v1/insights/flare-risk"),
  report: (days = 90) => json(S.Report, `/v1/reports/previsit?days=${days}`),
  weights: () => json(S.Weight, "/v1/weights"),
  saveWeight: (day: string, kg: number) => json(S.Weight, `/v1/weights/${day}`, send("PUT", { kg })),
  deleteWeight: (day: string) => raw(`/v1/weights/${day}`, { method: "DELETE" }),
  searchFoods: async (q: string) => (await json(S.FoodSearch, `/v1/foods/search?q=${encodeURIComponent(q)}`)).results,
};
