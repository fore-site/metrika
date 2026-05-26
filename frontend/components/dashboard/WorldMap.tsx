"use client";

import * as React from "react";
import { ComposableMap, Geographies, Geography } from "react-simple-maps";
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import world from "world-atlas/countries-110m.json";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import type { CountryItem } from "@/types/analytics";

function norm(s: string) {
  return s.trim().toLowerCase();
}

function fillFor(count: number, max: number) {
  if (!count || max <= 0) return "#F3F4F6";
  const t = Math.min(1, count / max);
  const alpha = 0.15 + 0.75 * t;
  return `rgba(99, 102, 241, ${alpha.toFixed(3)})`;
}

export function WorldMap(props: { data?: CountryItem[]; isLoading: boolean; error?: string | null }) {
  const [hover, setHover] = React.useState<{ name: string; visitors: number } | null>(null);

  const map = React.useMemo(() => {
    const m = new Map<string, number>();
    for (const c of props.data ?? []) m.set(norm(c.country), c.visitors);
    return m;
  }, [props.data]);

  const max = React.useMemo(() => Math.max(0, ...(props.data ?? []).map((c) => c.visitors)), [props.data]);

  return (
    <Card className="relative overflow-hidden p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-base font-semibold">Geography</div>
          <div className="mt-1 text-sm text-textSecondary">Where your visitors come from.</div>
        </div>
        {hover ? (
          <div className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs text-textSecondary shadow-sm">
            <div className="font-medium text-textPrimary">{hover.name}</div>
            <div>{hover.visitors} visitors</div>
          </div>
        ) : null}
      </div>

      <div className="mt-6 h-[320px]">
        {props.isLoading ? (
          <Skeleton className="h-full w-full" />
        ) : props.error ? (
          <div className="dot-grid grid h-full place-items-center rounded-xl border border-gray-200 bg-white">
            <div className="text-sm text-danger">{props.error}</div>
          </div>
        ) : (props.data?.length ?? 0) === 0 ? (
          <div className="dot-grid grid h-full place-items-center rounded-xl border border-gray-200 bg-white">
            <div className="text-sm text-textSecondary">No location data yet.</div>
          </div>
        ) : (
          <ComposableMap projectionConfig={{ scale: 150 }} style={{ width: "100%", height: "100%" }}>
            <Geographies geography={world}>
              {({ geographies }) =>
                geographies.map((geo) => {
                  const name = (geo.properties?.name ?? geo.properties?.NAME ?? "") as string;
                  const visitors = map.get(norm(name)) ?? 0;
                  return (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      fill={fillFor(visitors, max)}
                      stroke="#E5E7EB"
                      strokeWidth={0.5}
                      onMouseEnter={() => name && setHover({ name, visitors })}
                      onMouseLeave={() => setHover(null)}
                      style={{
                        default: { outline: "none" },
                        hover: { outline: "none", fill: fillFor(Math.max(visitors, max * 0.2), max) },
                        pressed: { outline: "none" },
                      }}
                    />
                  );
                })
              }
            </Geographies>
          </ComposableMap>
        )}
      </div>
    </Card>
  );
}

