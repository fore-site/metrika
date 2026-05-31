"use client";

import * as React from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { parseISO, format } from "date-fns";
import { DropdownMenu } from "@/components/ui/DropdownMenu";
import { setSearchParams } from "@/lib/url";

type Preset = "24h" | "day" | "7d" | "31d" | "91d" | "month-to-date" | "year-to-date";

function isPreset(v: string | null): v is Preset {
  return (
    v === "24h" || v === "day" || v === "7d" || v === "31d" || v === "91d" ||
    v === "month-to-date" || v === "year-to-date"
  );
}

export function DateRangePicker() {
  const pathname = usePathname();
  const router = useRouter();
  const sp = useSearchParams();

  const interval = sp.get("interval");
  const isCustom = interval === "custom";
  const preset: Preset = isPreset(interval) ? interval : "day";

  const [mode, setMode] = React.useState<"preset" | "custom">(isCustom ? "custom" : "preset");
  const [customStart, setCustomStart] = React.useState(sp.get("start") ?? "");
  const [customEnd, setCustomEnd] = React.useState(sp.get("end") ?? "");

  const today = new Date();
  const todayStr = today.toISOString().slice(0, 10);
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const yesterdayStr = yesterday.toISOString().slice(0, 10);


  React.useEffect(() => {
    setMode(isCustom ? "custom" : "preset");
    setCustomStart(sp.get("start") ?? "");
    setCustomEnd(sp.get("end") ?? "");
  }, [isCustom, sp]);

  const applyPreset = (value: Preset, dayOverride?: string) => {
    if (value === "day") {
      const day = dayOverride ?? new Date().toISOString().slice(0, 10); // YYYY‑MM‑DD
      const next = setSearchParams(sp as unknown as URLSearchParams, {
        interval: "day",
        day: day,
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
        <label className="sr-only">Range mode</label>
        <DropdownMenu label={mode === "preset" ? "Preset" : "Custom"}>
          <button
            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50"
            onClick={() => setMode("preset")}
          >
            Preset
          </button>
          <button
            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50"
            onClick={() => setMode("custom")}
          >
            Custom
          </button>
        </DropdownMenu>
      </div>

      {mode === "preset" ? (
        <div className="flex flex-1 items-center gap-2">
          <label className="sr-only" htmlFor="interval">
            Interval
          </label>
          <DropdownMenu
            label={
              (() => {
                if (preset === "day") {
                  const dayParam = sp.get("day");
                  if (!dayParam) return "Today";                 // fallback
                  // If the selected day is today, show "Today"
                  if (dayParam === todayStr) return "Today";
                  if (dayParam === yesterdayStr) return "Yesterday";
                  try {
                    return format(parseISO(dayParam), "MMM d, yyyy");
                  } catch {
                    return "Today";                               // parse error fallback
                  }
                }
                if (preset === "24h") return "Last 24 hours";
                if (preset === "7d") return "Last 7 days";
                if (preset === "31d") return "Last 31 days";
                if (preset === "91d") return "Last 91 days";
                if (preset === "month-to-date") return "Month to date";
                if (preset === "year-to-date") return "Year to date";
                return "Unknown";
              })()
            }
            className="w-fit max-w-[220px]"
          >
            <button
              className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 whitespace-nowrap"
              onClick={() => applyPreset("day")}
            >
              Today
            </button>
            <button className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 whitespace-nowrap" 
            onClick={() => applyPreset("day", yesterdayStr)}
            >
              Yesterday
            </button>
            <button
              className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 whitespace-nowrap"
              onClick={() => applyPreset("24h")}
            >
              Last 24 hours
            </button>
            <button
              className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 whitespace-nowrap"
              onClick={() => applyPreset("7d")}
            >
              Last 7 days
            </button>
            <button
              className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 whitespace-nowrap"
              onClick={() => applyPreset("31d")}
            >
              Last 31 days
            </button>
            <button
              className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 whitespace-nowrap"
              onClick={() => applyPreset("91d")}
            >
              Last 91 days
            </button>
            <button
              className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 whitespace-nowrap"
              onClick={() => applyPreset("month-to-date")}
            >
              Month to date
            </button>
            <button
              className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 whitespace-nowrap"
              onClick={() => applyPreset("year-to-date")}
            >
              Year to date
            </button>
          </DropdownMenu>
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

