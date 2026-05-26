"use client";

import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { formatDurationSeconds, formatNumber, formatPercent } from "@/lib/format";
import type { SummaryData } from "@/types/analytics";

function pctChange(current: number, previous: number) {
  if (!Number.isFinite(previous) || previous === 0) return null;
  const pct = ((current - previous) / previous) * 100;
  if (!Number.isFinite(pct)) return null;
  return pct;
}

function Trend({ pct }: { pct: number | null }) {
  if (pct === null) return <span className="text-xs text-textSecondary">—</span>;
  const up = pct >= 0;
  const Icon = up ? ArrowUpRight : ArrowDownRight;
  const color = up ? "text-success" : "text-danger";
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium ${color}`}>
      <Icon className="h-3.5 w-3.5" />
      {Math.abs(pct).toFixed(1)}%
    </span>
  );
}

function StatCard(props: { label: string; value: string; trendPct: number | null }) {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm text-textSecondary">{props.label}</div>
          <div className="mt-2 text-2xl font-semibold tracking-tight">{props.value}</div>
        </div>
        <Trend pct={props.trendPct} />
      </div>
    </Card>
  );
}

export function StatsRow(props: { current: SummaryData; previous?: SummaryData | null }) {
  const prev = props.previous ?? null;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <StatCard
        label="Unique Visitors"
        value={formatNumber(props.current.visitors)}
        trendPct={prev ? pctChange(props.current.visitors, prev.visitors) : null}
      />
      <StatCard
        label="Pageviews"
        value={formatNumber(props.current.pageviews)}
        trendPct={prev ? pctChange(props.current.pageviews, prev.pageviews) : null}
      />
      <StatCard
        label="Total Visits"
        value={formatNumber(props.current.total_visits)}
        trendPct={prev ? pctChange(props.current.total_visits, prev.total_visits) : null}
      />
      <StatCard
        label="Bounce Rate"
        value={formatPercent(props.current.bounce_rate)}
        trendPct={prev ? pctChange(props.current.bounce_rate, prev.bounce_rate) : null}
      />
      <StatCard
        label="Views / Visit"
        value={props.current.views_per_visit.toFixed(2)}
        trendPct={prev ? pctChange(props.current.views_per_visit, prev.views_per_visit) : null}
      />
      <StatCard
        label="Avg Duration"
        value={formatDurationSeconds(props.current.avg_duration_seconds)}
        trendPct={prev ? pctChange(props.current.avg_duration_seconds, prev.avg_duration_seconds) : null}
      />
    </div>
  );
}

