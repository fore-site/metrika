import { format, parseISO, subDays, differenceInCalendarDays } from "date-fns";

export type DateRange =
  | { kind: "preset"; interval: "24h" | "7d" | "31d" | "91d" | "month-to-date" | "year-to-date" }
  | { kind: "custom"; start: string; end: string }
  | {kind: "day"; day: string; };

export function getDefaultDateRange(): DateRange {
  const today = new Date().toISOString().slice(0, 10);
  return { kind: "day", day: today };
}

export function toApiQuery(range: DateRange): Record<string, string> {
  if (range.kind === "preset") return { interval: range.interval };
  if (range.kind === "day") return { interval: "day", day: range.day };
  return { interval: "custom", start: range.start, end: range.end };
}

export function safeParseDate(iso: string | null) {
  if (!iso) return null;
  try {
    return parseISO(iso);
  } catch {
    return null;
  }
}

export function getPreviousRange(range: DateRange): DateRange | null {
  if (range.kind === "preset") {
    if (range.interval === "24h") return null;
    if (range.interval === "7d") {
      const end = subDays(new Date(), 1);
      const start = subDays(end, 7);
      const prevEnd = subDays(start, 1);
      const prevStart = subDays(prevEnd, 7);
      return { kind: "custom", start: format(prevStart, "yyyy-MM-dd"), end: format(prevEnd, "yyyy-MM-dd") };
    }
    if (range.interval === "31d" || range.interval === "91d") {
      const days = range.interval === "31d" ? 31 : 91;
      const end = subDays(new Date(), 1);
      const start = subDays(end, days);
      const prevEnd = subDays(start, 1);
      const prevStart = subDays(prevEnd, days);
      return { kind: "custom", start: format(prevStart, "yyyy-MM-dd"), end: format(prevEnd, "yyyy-MM-dd") };
    }
    if (range.interval === "month-to-date") {
      const now = new Date();
      const start = new Date(now.getFullYear(), now.getMonth(), 1);
      const end = subDays(now, 1);
      const days = Math.max(1, differenceInCalendarDays(end, start));
      const prevEnd = subDays(start, 1);
      const prevStart = subDays(prevEnd, days);
      return { kind: "custom", start: format(prevStart, "yyyy-MM-dd"), end: format(prevEnd, "yyyy-MM-dd") };
    }
    if (range.interval === "year-to-date") {
      const now = new Date();
      const start = new Date(now.getFullYear(), 0, 1);
      const end = subDays(now, 1);
      const days = Math.max(1, differenceInCalendarDays(end, start));
      const prevEnd = subDays(start, 1);
      const prevStart = subDays(prevEnd, days);
      return { kind: "custom", start: format(prevStart, "yyyy-MM-dd"), end: format(prevEnd, "yyyy-MM-dd") };
    }
  }
  if (range.kind === "custom") {
    const start = safeParseDate(range.start);
    const end = safeParseDate(range.end);
    if (!start || !end) return null;
    const days = Math.max(1, differenceInCalendarDays(end, start));
    const prevEnd = subDays(start, 1);
    const prevStart = subDays(prevEnd, days);
    return { kind: "custom", start: format(prevStart, "yyyy-MM-dd"), end: format(prevEnd, "yyyy-MM-dd") };
  }

  if (range.kind === "day") {
    const day = safeParseDate(range.day);
    if (!day) return null;
    // compare to the same day last week
    const prevDay = subDays(day, 7);
    return { kind: "custom", start: format(prevDay, "yyyy-MM-dd"), end: format(prevDay, "yyyy-MM-dd") };
  }
  return null;
}

