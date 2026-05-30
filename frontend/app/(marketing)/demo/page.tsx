"use client";

import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import type {
  SummaryData,
  TimeseriesEntry,
  CountryItem,
  RegionItem,
  CityItem,
  DeviceItem,
  OSItem,
  BrowserItem,
  TopPage,
  TopReferrer,
} from "@/types/analytics";
import { StatsRow } from "@/components/dashboard/StatsRow";
import { TimeseriesChart } from "@/components/dashboard/TimeseriesChart";
import { WorldMap } from "@/components/dashboard/WorldMap";
import { PaginatedCardTable } from "@/components/dashboard/PaginatedCardTable";
import { getPreviousRange, toApiQuery } from "@/lib/dates";
import { useDateRangeFromSearch } from "@/components/dashboard/useDashboardParams";
import { ApiError } from "@/lib/errors";
import { DemoTopNav } from "@/components/demo/DemoTopNav";

const DEMO_API_BASE =
  (process.env.NEXT_PUBLIC_API_URL || "https://metrika-api.up.railway.app") +
  "/api/stats/demo/0"; // site_id is ignored by backend

function buildStatsUrl(endpoint: string, query: Record<string, string>) {
  const params = new URLSearchParams(query);
  return `${DEMO_API_BASE}/${endpoint}/?${params.toString()}`;
}

function buildStatsListUrl(
  endpoint: string,
  query: Record<string, string>,
  paging: { limit: number; offset: number }
) {
  const params = new URLSearchParams(query);
  params.set("limit", String(paging.limit));
  params.set("offset", String(paging.offset));
  return `${DEMO_API_BASE}/${endpoint}/?${params.toString()}`;
}

async function fetchDemoData<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    const json = await res.json().catch(() => null);
    throw new ApiError(res.status, json?.message ?? "Request failed");
  }
  const json = await res.json();
  if (json.status !== "success") {
    throw new ApiError(res.status, json.message ?? "Request failed");
  }
  return json.data as T;
}

async function fetchDemoEnvelope<T>(url: string): Promise<any> {
  const res = await fetch(url);
  const json = await res.json().catch(() => null);
  if (!res.ok || !json || json.status !== "success") {
    throw new ApiError(res?.status ?? 500, json?.message ?? "Request failed");
  }
  return json; // full envelope, used for timeseries meta
}

export default function DemoPage() {
  const dateRange = useDateRangeFromSearch();

  const query = toApiQuery(dateRange);
  const prevRange = getPreviousRange(dateRange);
  const prevQuery = prevRange ? toApiQuery(prevRange) : null;

  // Summary
  const summaryQuery = useQuery({
    queryKey: ["demo-summary", query],
    queryFn: () => fetchDemoData<SummaryData>(buildStatsUrl("summary", query)),
  });
  const prevSummaryQuery = useQuery({
    queryKey: ["demo-summary-prev", prevQuery],
    queryFn: () => fetchDemoData<SummaryData>(buildStatsUrl("summary", prevQuery!)),
    enabled: !!prevQuery,
  });

  // Timeseries (full envelope for meta.precision)
  const timeseriesQuery = useQuery({
    queryKey: ["demo-timeseries", query],
    queryFn: () => fetchDemoEnvelope<TimeseriesEntry[]>(buildStatsUrl("timeseries", query)),
  });
  const envelope = timeseriesQuery.data;
  const timeseriesData: TimeseriesEntry[] = envelope?.data ?? [];
  const precision = envelope?.meta?.precision as
    "hour" | "day" | "month" | "year" | undefined;

  // Countries (for WorldMap and table)
  const countriesQuery = useQuery({
    queryKey: ["demo-countries", query],
    queryFn: () =>
      fetchDemoData<CountryItem[]>(
        buildStatsListUrl("countries", query, { limit: 200, offset: 0 })
      ),
  });

  // Tables (regions, cities, devices, os, browsers, pages, referrers)
  const tableQueryBase = (endpoint: string) => buildStatsListUrl(endpoint, query, { limit: 5, offset: 0 });

  // Render helpers
  const err = (e: unknown) => (e instanceof ApiError ? e.message : "Unable to load.");

  return (
    <div className="min-h-screen bg-background">
      <DemoTopNav />
      <main className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6">
        {/* Stats Row */}
        {summaryQuery.isLoading ? (
          <Card className="dot-grid h-32" />
        ) : summaryQuery.error ? (
          <EmptyState title="Failed to load summary" description={err(summaryQuery.error)} />
        ) : summaryQuery.data ? (
          <StatsRow current={summaryQuery.data} previous={prevSummaryQuery.data} />
        ) : null}

        {/* Timeseries Chart */}
        <TimeseriesChart
          data={timeseriesData.map((d) => ({
            label: d.date ?? d.hour ?? d.month ?? d.year ?? "",
            visitors: d.visitors,
          }))}
          precision={precision ?? "day"}
          isLoading={timeseriesQuery.isLoading}
          error={timeseriesQuery.error ? err(timeseriesQuery.error) : null}
        />

        {/* World Map */}
        <WorldMap
          data={countriesQuery.data}
          isLoading={countriesQuery.isLoading}
          error={countriesQuery.error ? err(countriesQuery.error) : null}
        />

        {/* Geography tables (3 cols) */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <PaginatedCardTable<CountryItem>
            title="Countries"
            queryKey={["demo-countries-table", query]}
            initialPath={tableQueryBase("countries")}
            columns={[
              { header: "Country", render: (r) => r.country },
              { header: "Visitors", className: "text-right", render: (r) => r.visitors.toLocaleString() },
            ]}
            getRowKey={(r) => r.country}
          />
          <PaginatedCardTable<RegionItem>
            title="Top Regions"
            queryKey={["demo-regions-table", query]}
            initialPath={tableQueryBase("top-regions")}
            columns={[
              { header: "Region", render: (r) => r.region || "—" },
              { header: "Visitors", className: "text-right", render: (r) => r.visitors.toLocaleString() },
            ]}
            getRowKey={(r) => r.region}
          />
          <PaginatedCardTable<CityItem>
            title="Top Cities"
            queryKey={["demo-cities-table", query]}
            initialPath={tableQueryBase("top-cities")}
            columns={[
              { header: "City", render: (r) => r.city || "—" },
              { header: "Visitors", className: "text-right", render: (r) => r.visitors.toLocaleString() },
            ]}
            getRowKey={(r) => r.city}
          />
        </div>

        {/* Technology tables (3 cols) */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <PaginatedCardTable<DeviceItem>
            title="Devices"
            queryKey={["demo-devices-table", query]}
            initialPath={tableQueryBase("devices")}
            columns={[
              { header: "Device", render: (r) => r.device_type || "—" },
              { header: "Visitors", className: "text-right", render: (r) => r.visitors.toLocaleString() },
            ]}
            getRowKey={(r) => r.device_type}
          />
          <PaginatedCardTable<OSItem>
            title="OS"
            queryKey={["demo-os-table", query]}
            initialPath={tableQueryBase("os")}
            columns={[
              { header: "OS", render: (r) => r.os || "—" },
              { header: "Visitors", className: "text-right", render: (r) => r.visitors.toLocaleString() },
            ]}
            getRowKey={(r) => r.os}
          />
          <PaginatedCardTable<BrowserItem>
            title="Browsers"
            queryKey={["demo-browsers-table", query]}
            initialPath={tableQueryBase("browsers")}
            columns={[
              { header: "Browser", render: (r) => r.browser || "—" },
              { header: "Visitors", className: "text-right", render: (r) => r.visitors.toLocaleString() },
            ]}
            getRowKey={(r) => r.browser}
          />
        </div>

        {/* Content tables (2 cols) */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <PaginatedCardTable<TopPage>
            title="Top Pages"
            queryKey={["demo-top-pages-table", query]}
            initialPath={tableQueryBase("top-pages")}
            columns={[
              { header: "URL", render: (r) => <span className="truncate">{r.url}</span> },
              { header: "Visitors", className: "text-right", render: (r) => r.visitors.toLocaleString() },
              { header: "Pageviews", className: "text-right", render: (r) => r.pageviews.toLocaleString() },
            ]}
            getRowKey={(r) => r.url}
          />
          <PaginatedCardTable<TopReferrer>
            title="Top Referrers"
            queryKey={["demo-top-referrers-table", query]}
            initialPath={tableQueryBase("top-referrers")}
            columns={[
              { header: "Source", render: (r) => <span className="truncate">{r.source}</span> },
              { header: "Medium", render: (r) => <span className="truncate">{r.medium}</span> },
              { header: "Visitors", className: "text-right", render: (r) => r.visitors.toLocaleString() },
            ]}
            getRowKey={(r) => `${r.source}-${r.medium}`}
          />
        </div>
      </main>
    </div>
  );
}