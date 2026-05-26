"use client";

import * as React from "react";
import { useSearchParams } from "next/navigation";
import type { DateRange } from "@/lib/dates";
import { getDefaultDateRange } from "@/lib/dates";

export function useSelectedSiteId() {
  const sp = useSearchParams();
  const site = sp.get("site");
  return site ? Number(site) : null;
}

export function useDateRangeFromSearch(): DateRange {
  const sp = useSearchParams();
  const interval = sp.get("interval");
  const start = sp.get("start");
  const end = sp.get("end");

  return React.useMemo(() => {
    if (interval === "custom" && start && end) return { kind: "custom", start, end } as const;
    if (
      interval === "24h" ||
      interval === "7d" ||
      interval === "31d" ||
      interval === "91d" ||
      interval === "month-to-date" ||
      interval === "year-to-date"
    ) {
      return { kind: "preset", interval } as const;
    }
    return getDefaultDateRange();
  }, [end, interval, start]);
}

