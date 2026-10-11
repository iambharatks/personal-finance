import { describe, expect, it } from "vitest";

import { fyLabel, fyStartYear, iso, monthRange, rangeOptions, resolveRange } from "./filters";
import { dayLabel, inr, inrExact, monthLabel, percent } from "./format";

const day = (text: string) => new Date(`${text}T12:00:00`);

describe("financial year", () => {
  it("starts on 1 April", () => {
    expect(fyStartYear(day("2026-03-31"))).toBe(2025);
    expect(fyStartYear(day("2026-04-01"))).toBe(2026);
    expect(fyStartYear(day("2026-10-11"))).toBe(2026);
    expect(fyStartYear(day("2027-01-15"))).toBe(2026);
  });

  it("is labelled by both years", () => {
    expect(fyLabel(2025)).toBe("FY 2025-26");
    expect(fyLabel(1999)).toBe("FY 1999-00");
  });

  it("resolves current and previous", () => {
    const today = day("2026-10-11");
    expect(resolveRange("fy-current", today)).toEqual({ from: "2026-04-01", to: "2027-03-31" });
    expect(resolveRange("fy-previous", today)).toEqual({ from: "2025-04-01", to: "2026-03-31" });
    expect(rangeOptions(today).map((o) => o.label)).toContain("FY 2025-26");
  });
});

describe("month presets", () => {
  it("cover whole months", () => {
    const today = day("2026-10-11");
    expect(resolveRange("this-month", today)).toEqual({ from: "2026-10-01", to: "2026-10-31" });
    expect(resolveRange("last-3-months", today)).toEqual({ from: "2026-08-01", to: "2026-10-31" });
    expect(resolveRange("this-year", today)).toEqual({ from: "2026-01-01", to: "2026-12-31" });
    expect(resolveRange("all", today)).toEqual({});
  });

  it("cross a year boundary", () => {
    expect(resolveRange("last-6-months", day("2026-02-10"))).toEqual({
      from: "2025-09-01",
      to: "2026-02-28",
    });
  });

  it("know month lengths", () => {
    expect(monthRange("2024-02")).toEqual({ from: "2024-02-01", to: "2024-02-29" });
    expect(monthRange("2025-12")).toEqual({ from: "2025-12-01", to: "2025-12-31" });
    expect(iso(day("2026-01-05"))).toBe("2026-01-05");
  });
});

describe("formatting", () => {
  it("uses Indian digit grouping", () => {
    expect(inr(3009965)).toBe("₹30,09,965");
    expect(inr(388446.46)).toBe("₹3,88,446");
    expect(inrExact(388446.46)).toBe("₹3,88,446.46");
    expect(inr(-1500)).toBe("-₹1,500");
  });

  it("formats dates and ratios", () => {
    expect(monthLabel("2025-04")).toBe("Apr 25");
    expect(dayLabel("2025-04-03")).toBe("3 Apr 2025");
    expect(percent(0.5695)).toBe("57.0%");
    expect(percent(null)).toBe("–");
  });
});
