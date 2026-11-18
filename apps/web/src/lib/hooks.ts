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
  weights: ["weights"] as const,
  medications: ["medications"] as const,
  appointments: ["appointments"] as const,
};

/** Query keys to refresh after the diary, a period or a stressful period changes. */
export const PERSONAL_KEYS = [["risk"], ["periods"], ["days"], ["patterns"], ["diary"], ["me"], ["report"], ["foodGuide"], ["mealPlan"], ["weights"], ["medications"], ["appointments"]] as const;

/** A dish's name in the chosen language: known dishes come from the food guide, others keep what was typed. */
export function useDishName(lang: string): (dish: { dish_id: string | null; name: string }) => string {
  const guide = useQuery({ queryKey: ["foodGuide"], queryFn: api.foodGuide, staleTime: 5 * 60_000 }).data;
  return (dish) => {
    const known = dish.dish_id ? guide?.find((g) => g.dish_id === dish.dish_id) : undefined;
    return known ? (lang === "bn" ? known.name_bn : known.name_en) : dish.name;
  };
}
