import { useQuery } from "@tanstack/react-query";
import { api } from "./api";

/** "Today" as the server sees it (Asia/Dhaka), so the diary date never drifts from the backend's. */
export function useToday(): string | undefined {
  return useQuery({ queryKey: ["today"], queryFn: async () => (await api.days(1)).today, staleTime: 5 * 60_000 }).data;
}

export const keys = {
  risk: ["risk"] as const,
  periods: ["periods"] as const,
  days: (limit: number) => ["days", limit] as const,
  diary: (date: string) => ["diary", date] as const,
  patterns: (scope: string) => ["patterns", scope] as const,
  mealChecks: ["mealChecks"] as const,
  stressPeriods: ["stressPeriods"] as const,
};

/** Query keys to refresh after the diary, a period or a stressful period changes. */
export const PERSONAL_KEYS = [["risk"], ["periods"], ["days"], ["patterns"], ["diary"], ["me"], ["report"], ["foodGuide"], ["mealPlan"]] as const;
