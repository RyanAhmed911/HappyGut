import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import bn from "../locales/bn.json";
import en from "../locales/en.json";

type Tree = { [key: string]: string | Tree };

function flatten(tree: Tree, prefix = ""): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [key, value] of Object.entries(tree)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (typeof value === "string") out[path] = value;
    else Object.assign(out, flatten(value, path));
  }
  return out;
}

function sources(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return name === "test" || name === "locales" ? [] : sources(path);
    return /\.tsx?$/.test(name) ? [path] : [];
  });
}

const EN = flatten(en);
const BN = flatten(bn);

describe("locales (Constitution VI: every string in Bangla and English)", () => {
  it("have exactly the same keys", () => {
    expect(Object.keys(BN).sort()).toEqual(Object.keys(EN).sort());
  });

  it("use the same placeholders in both languages", () => {
    const vars = (s: string): string[] => [...s.matchAll(/\{\{(\w+)\}\}/g)].map((m) => m[1]!).sort();
    for (const key of Object.keys(EN)) expect(vars(BN[key] ?? ""), key).toEqual(vars(EN[key]!));
  });

  it("Bangla strings are in Bangla script", () => {
    const latinOnly = Object.entries(BN).filter(([, v]) => !/[ঀ-৿]/.test(v));
    expect(latinOnly).toEqual([]);
  });

  it("never call a food safe or use causal wording", () => {
    for (const [key, value] of Object.entries(EN)) {
      if (key === "settings.safety_1" || key === "welcome.f_check_text") continue; // these state the rule itself
      expect(/\bsafe\b|\bcaused\b/i.test(value), key).toBe(false);
    }
    for (const [key, value] of Object.entries(BN)) {
      if (key === "settings.safety_1" || key === "welcome.f_check_text") continue;
      expect(/নিরাপদ/.test(value), key).toBe(false);
    }
  });

  it("define every key the source code uses", () => {
    const files = sources(join(__dirname, ".."));
    const missing = new Set<string>();
    const dynamicPrefixes = new Set<string>();
    for (const file of files) {
      const text = readFileSync(file, "utf8");
      for (const m of text.matchAll(/["'`]((?:app|nav|verdict|welcome|today|check|redflag|diary|patterns|risk|gut|history|report|settings|notice|foods|reminder)\.[a-zA-Z0-9_]+)["'`]/g)) {
        if (!(m[1]! in EN)) missing.add(m[1]!);
      }
      for (const m of text.matchAll(/`((?:[a-zA-Z]+)\.(?:[a-zA-Z0-9_]*))\$\{/g)) dynamicPrefixes.add(m[1]!);
    }
    expect([...missing]).toEqual([]);
    for (const prefix of dynamicPrefixes) {
      expect(Object.keys(EN).some((k) => k.startsWith(prefix)), prefix).toBe(true);
    }
  });
});
