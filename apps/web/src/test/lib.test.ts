import { describe, expect, it } from "vitest";
import { addDays, clock, daysBetween, isoDay, num, parseDay, shortDate } from "../lib/format";
import { DiarySaved, Patterns, VerdictEvent } from "../lib/schemas";
import { parseSseBlock } from "../lib/sse";

describe("sse", () => {
  it("parses an event block", () => {
    expect(parseSseBlock('event: verdict\ndata: {"verdict":"caution"}')).toEqual({ event: "verdict", data: { verdict: "caution" } });
  });
  it("keeps Bangla text and ignores broken blocks", () => {
    expect(parseSseBlock('event: not_food\ndata: {"message":"খাবার নেই"}')?.data).toEqual({ message: "খাবার নেই" });
    expect(parseSseBlock("event: x\ndata: {oops")).toBeNull();
    expect(parseSseBlock(": comment")).toBeNull();
  });
});

describe("format", () => {
  it("writes numbers in Bangla digits for bn", () => {
    expect(num(15, "bn")).toBe("১৫");
    expect(num(15, "en")).toBe("15");
    expect(num(7.25, "bn", 1)).toBe("৭.৩");
  });
  it("does date arithmetic on calendar days", () => {
    expect(addDays("2026-11-30", 1)).toBe("2026-12-01");
    expect(addDays("2026-03-01", -1)).toBe("2026-02-28");
    expect(daysBetween("2026-11-15", "2026-11-18")).toBe(3);
    expect(isoDay(parseDay("2026-11-15"))).toBe("2026-11-15");
  });
  it("formats dates and clock times per language", () => {
    expect(shortDate("2026-11-15", "en")).toBe("15 Nov");
    expect(shortDate("2026-11-15", "bn")).toMatch(/১৫/);
    expect(clock("23:30", "en")).toMatch(/23:30|11:30/);
  });
});

describe("schemas", () => {
  it("accept the API's verdict event and reject an unknown verdict", () => {
    const dish = {
      dish_id: "dish.kacchi_biryani", name: "Kacchi biryani", perceived_name: "kacchi", verdict: "likely_trigger", risk: 0.9, confidence: 0.9,
      reason: "personal", contributions: { guideline: 0.3, personal: 0.9 }, components: [], evidence_ids: ["personal:fat"], alternative: null,
    };
    const event = { verdict: "likely_trigger", risk: 0.9, confidence: 0.9, engine_version: "engine-v0.2", dishes: [dish], clarifying_question: null };
    expect(VerdictEvent.parse(event).dishes[0]?.name).toBe("Kacchi biryani");
    expect(() => VerdictEvent.parse({ ...event, verdict: "safe" })).toThrow();
  });
  it("accept empty pattern results and a red-flag diary response", () => {
    expect(Patterns.parse({ scope: "all", days_logged: 3, min_days: 14, enough_data: false, index_name: "HBI", results: [], is_synthetic: true }).results).toEqual([]);
    expect(() => DiarySaved.parse({ entry: {}, red_flag: null, comparison: null })).toThrow();
  });
});
