"use client";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatNumber } from "@/lib/format";
import { parseISO, format } from "date-fns";

export type TimeseriesPoint = {
  label: string;
  visitors: number;
};

type Precision = "hour" | "day" | "month" | "year";

function formatLabel(raw: string, precision: Precision): string {
  try {
    const dt = parseISO(raw);
    switch (precision) {
      case "hour":
        // Show only the hour, e.g. "3 am"
        return format(dt, "h aaa");      // "3 am"
      case "day":
        // Show date, no year, e.g. "20 Apr"
        return format(dt, "d MMM");
      case "month":
        // Show month and year, e.g. "Apr 2026"
        return format(dt, "MMM yyyy");
      case "year":
        // Show only year, e.g. "2026"
        return format(dt, "yyyy");
      default:
        return raw;
    }
  } catch {
    return raw;
  }
}

export function TimeseriesChart(props: {
  data?: TimeseriesPoint[];
  isLoading: boolean;
  error?: string | null;
  precision?: Precision;   // optional, defaults to 'day'
}) {
  const precision = props.precision ?? "day";

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-base font-semibold">Visitors over time</div>
          <div className="mt-1 text-sm text-textSecondary">
            Unique visitors for the selected range.
          </div>
        </div>
      </div>

      <div className="mt-6 h-72">
        {props.isLoading ? (
          <div className="h-full">
            <Skeleton className="h-full w-full" />
          </div>
        ) : props.error ? (
          <div className="dot-grid grid h-full place-items-center rounded-xl border border-gray-200 bg-white">
            <div className="text-sm text-danger">{props.error}</div>
          </div>
        ) : (props.data?.length ?? 0) === 0 ? (
          <div className="dot-grid grid h-full place-items-center rounded-xl border border-gray-200 bg-white">
            <div className="text-sm text-textSecondary">
              No timeseries data yet for this range.
            </div>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
            <LineChart
              data={props.data}
              margin={{ top: 10, right: 16, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="visitorsStroke" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#6366F1" stopOpacity={0.9} />
                  <stop offset="100%" stopColor="#8B5CF6" stopOpacity={0.9} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="5 5" stroke="#E5E7EB" />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 12 }}
                stroke="#6B7280"
                tickFormatter={(value) => formatLabel(String(value), precision)}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                stroke="#6B7280"
                tickFormatter={(v) => formatNumber(Number(v))}
              />
              <Tooltip
                formatter={(value) => formatNumber(Number(value))}
                labelFormatter={(label) => formatLabel(String(label), precision)}
                contentStyle={{ borderRadius: 12, borderColor: "#E5E7EB" }}
              />
              <Line
                type="monotone"
                dataKey="visitors"
                name="Visitors"
                stroke="url(#visitorsStroke)"
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </Card>
  );
} 