"use client";

import * as React from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { setSearchParams } from "@/lib/url";

type Preset = "24h" | "today" | "7d" | "31d" | "91d" | "month-to-date" | "year-to-date";

function isPreset(v: string | null): v is Preset {
  return (
    v === "24h" || v === "today" || v === "7d" || v === "31d" || v === "91d" ||
    v === "month-to-date" || v === "year-to-date"
  );
}

export function DateRangePicker() {
  const pathname = usePathname();
  const router = useRouter();
  const sp = useSearchParams();

  const interval = sp.get("interval");
  const isCustom = interval === "custom";
  const preset: Preset = isPreset(interval) ? interval : "31d";

  const [mode, setMode] = React.useState<"preset" | "custom">(isCustom ? "custom" : "preset");
  const [customStart, setCustomStart] = React.useState(sp.get("start") ?? "");
  const [customEnd, setCustomEnd] = React.useState(sp.get("end") ?? "");

  React.useEffect(() => {
    setMode(isCustom ? "custom" : "preset");
    setCustomStart(sp.get("start") ?? "");
    setCustomEnd(sp.get("end") ?? "");
  }, [isCustom, sp]);

  const applyPreset = (value: Preset) => {
    if (value === "today") {
      const today = new Date().toISOString().slice(0, 10); // YYYY‑MM‑DD
      const next = setSearchParams(sp as unknown as URLSearchParams, {
        interval: "day",
        day: today,
        start: null,
        end: null,
      });
      router.replace(`${pathname}?${next.toString()}`);
      return;
    }

    const next = setSearchParams(sp as unknown as URLSearchParams, { interval: value, start: null, end: null });
    router.replace(`${pathname}?${next.toString()}`);
  };

  const applyCustom = () => {
    if (!customStart || !customEnd) return;

    // Single‑day pick → use interval=day
    if (customStart === customEnd) {
      const next = setSearchParams(sp as unknown as URLSearchParams, {
        interval: "day",
        day: customStart,
        start: null,
        end: null,
      });
      router.replace(`${pathname}?${next.toString()}`);
      return;
    }
    const next = setSearchParams(sp as unknown as URLSearchParams, {
      interval: "custom",
      start: customStart,
      end: customEnd,
    });
    router.replace(`${pathname}?${next.toString()}`);
  };

  return (
    <div className="flex w-full max-w-md items-center justify-end gap-2">
      <div className="flex flex-1 items-center gap-2">
        <label className="sr-only" htmlFor="rangeMode">
          Range mode
        </label>
        <select
          id="rangeMode"
          className="input h-11 w-40"
          value={mode}
          onChange={(e) => setMode(e.target.value as "preset" | "custom")}
        >
          <option value="preset">Preset</option>
          <option value="custom">Custom</option>
        </select>
      </div>

      {mode === "preset" ? (
        <div className="flex flex-1 items-center gap-2">
          <label className="sr-only" htmlFor="interval">
            Interval
          </label>
          <select
            id="interval"
            className="input h-11 w-full"
            value={preset}
            onChange={(e) => applyPreset(e.target.value as Preset)}
          >
            <option value="today">Today</option>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="31d">Last 31 days</option>
            <option value="91d">Last 91 days</option>
            <option value="month-to-date">Month to date</option>
            <option value="year-to-date">Year to date</option>
          </select>
        </div>
      ) : (
        <div className="flex flex-1 items-center gap-2">
          <input
            className="input h-11"
            type="date"
            value={customStart}
            onChange={(e) => setCustomStart(e.target.value)}
            aria-label="Start date"
          />
          <input
            className="input h-11"
            type="date"
            value={customEnd}
            onChange={(e) => setCustomEnd(e.target.value)}
            aria-label="End date"
          />
          <button
            className="btn btn-secondary h-11 px-4 py-0"
            onClick={applyCustom}
            disabled={!customStart || !customEnd}
            type="button"
          >
            Apply
          </button>
        </div>
      )}
    </div>
  );
}

