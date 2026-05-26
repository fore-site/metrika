"use client";

import * as React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from "recharts";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatNumber } from "@/lib/format";
export type TimeseriesPoint = {
  label: string;
  visitors: number;
  pageviews: number;
};

export function TimeseriesChart(props: {
  data?: TimeseriesPoint[];
  isLoading: boolean;
  error?: string | null;
}) {
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-base font-semibold">Traffic over time</div>
          <div className="mt-1 text-sm text-textSecondary">Visitors and pageviews for the selected range.</div>
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
            <div className="text-sm text-textSecondary">No timeseries data yet for this range.</div>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={props.data} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="visitorsStroke" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#6366F1" stopOpacity={0.9} />
                  <stop offset="100%" stopColor="#8B5CF6" stopOpacity={0.9} />
                </linearGradient>
                <linearGradient id="pageviewsStroke" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#10B981" stopOpacity={0.9} />
                  <stop offset="100%" stopColor="#34D399" stopOpacity={0.9} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="5 5" stroke="#E5E7EB" />
              <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="#6B7280" />
              <YAxis tick={{ fontSize: 12 }} stroke="#6B7280" tickFormatter={(v) => formatNumber(Number(v))} />
              <Tooltip
                formatter={(value) => formatNumber(Number(value))}
                contentStyle={{ borderRadius: 12, borderColor: "#E5E7EB" }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="visitors"
                name="Visitors"
                stroke="url(#visitorsStroke)"
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="pageviews"
                name="Pageviews"
                stroke="url(#pageviewsStroke)"
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
