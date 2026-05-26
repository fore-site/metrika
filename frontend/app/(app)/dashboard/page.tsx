"use client";

import * as React from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { useApi } from "@/lib/useApi";
import type { Site } from "@/types/site";
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
import { CreateSiteCard } from "@/components/dashboard/CreateSiteCard";
import { getPreviousRange, toApiQuery } from "@/lib/dates";
import { useDateRangeFromSearch } from "@/components/dashboard/useDashboardParams";
import { ApiError } from "@/lib/errors";

function buildStatsUrl(siteId: number, endpoint: string, query: Record<string, string>) {
  const params = new URLSearchParams(query);
  return `/api/stats/${siteId}/${endpoint}/?${params.toString()}`;
}

function buildStatsListUrl(siteId: number, endpoint: string, query: Record<string, string>, paging: { limit: number; offset: number }) {
  const params = new URLSearchParams(query);
  params.set("limit", String(paging.limit));
  params.set("offset", String(paging.offset));
  return `/api/stats/${siteId}/${endpoint}/?${params.toString()}`;
}

export default function DashboardPage() {
  const api = useApi();
  const sp = useSearchParams();
  const dateRange = useDateRangeFromSearch();

  const sitesQuery = useQuery({
    queryKey: ["sites"],
    queryFn: () => api.get<Site[]>("/api/sites/"),
  });

  const selectedSiteId = Number(sp.get("site") ?? "") || (sitesQuery.data?.[0] ? Number(sitesQuery.data[0].id) : 0);

  if (sitesQuery.isLoading) {
    return (
      <div className="grid gap-6">
        <Card className="dot-grid h-28" />
        <Card className="dot-grid h-80" />
      </div>
    );
  }

  if ((sitesQuery.data?.length ?? 0) === 0) {
    return <CreateSiteCard />;
  }

  if (!selectedSiteId) {
    return <EmptyState title="Select a site" description="Choose a site from the selector to view analytics." />;
  }

  const query = toApiQuery(dateRange);
  const prevRange = getPreviousRange(dateRange);
  const prevQuery = prevRange ? toApiQuery(prevRange) : null;

  const summaryQuery = useQuery({
    queryKey: ["summary", selectedSiteId, query],
    queryFn: () => api.get<SummaryData>(buildStatsUrl(selectedSiteId, "summary", query)),
  });

  const prevSummaryQuery = useQuery({
    queryKey: ["summary-prev", selectedSiteId, prevQuery],
    enabled: Boolean(prevQuery),
    queryFn: () => api.get<SummaryData>(buildStatsUrl(selectedSiteId, "summary", prevQuery!)),
  });

  const timeseriesQuery = useQuery({
    queryKey: ["timeseries", selectedSiteId, query],
    queryFn: () => api.get<TimeseriesEntry[]>(buildStatsUrl(selectedSiteId, "timeseries", query)),
  });

  const countriesQuery = useQuery({
    queryKey: ["countries", selectedSiteId, query],
    queryFn: () => api.get<CountryItem[]>(buildStatsListUrl(selectedSiteId, "countries", query, { limit: 200, offset: 0 })),
  });

  const err = (e: unknown) => (e instanceof ApiError ? e.message : "Unable to load.");

  return (
    <div className="space-y-6">
      {summaryQuery.isLoading ? (
        <Card className="dot-grid h-32" />
      ) : summaryQuery.error ? (
        <EmptyState title="Failed to load summary" description={err(summaryQuery.error)} />
      ) : summaryQuery.data ? (
        <StatsRow current={summaryQuery.data} previous={prevSummaryQuery.data} />
      ) : null}

      <TimeseriesChart
        data={(timeseriesQuery.data ?? []).map((d) => ({
          label: d.date ?? d.hour ?? d.month ?? d.year ?? "",
          visitors: d.visitors,
          pageviews: d.pageviews,
        }))}
        isLoading={timeseriesQuery.isLoading}
        error={timeseriesQuery.error ? err(timeseriesQuery.error) : null}
      />

      <WorldMap
        data={countriesQuery.data}
        isLoading={countriesQuery.isLoading}
        error={countriesQuery.error ? err(countriesQuery.error) : null}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <PaginatedCardTable<CountryItem>
          title="Countries"
          queryKey={["countries-table", selectedSiteId, query]}
          initialPath={buildStatsListUrl(selectedSiteId, "countries", query, { limit: 5, offset: 0 })}
          columns={[
            { header: "Country", render: (r) => r.country },
            { header: "Visitors", className: "text-right", render: (r) => r.visitors.toLocaleString() },
          ]}
          getRowKey={(r) => r.country}
        />
        <PaginatedCardTable<RegionItem>
          title="Top Regions"
          queryKey={["regions", selectedSiteId, query]}
          initialPath={buildStatsListUrl(selectedSiteId, "top-regions", query, { limit: 5, offset: 0 })}
          columns={[
            { header: "Region", render: (r) => r.region || "—" },
            { header: "Visitors", className: "text-right", render: (r) => r.visitors.toLocaleString() },
          ]}
          getRowKey={(r) => r.region}
        />
        <PaginatedCardTable<CityItem>
          title="Top Cities"
          queryKey={["cities", selectedSiteId, query]}
          initialPath={buildStatsListUrl(selectedSiteId, "top-cities", query, { limit: 5, offset: 0 })}
          columns={[
            { header: "City", render: (r) => r.city || "—" },
            { header: "Visitors", className: "text-right", render: (r) => r.visitors.toLocaleString() },
          ]}
          getRowKey={(r) => r.city}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <PaginatedCardTable<DeviceItem>
          title="Devices"
          queryKey={["devices", selectedSiteId, query]}
          initialPath={buildStatsListUrl(selectedSiteId, "devices", query, { limit: 5, offset: 0 })}
          columns={[
            { header: "Device", render: (r) => r.device_type || "—" },
            { header: "Visitors", className: "text-right", render: (r) => r.visitors.toLocaleString() },
          ]}
          getRowKey={(r) => r.device_type}
        />
        <PaginatedCardTable<OSItem>
          title="OS"
          queryKey={["os", selectedSiteId, query]}
          initialPath={buildStatsListUrl(selectedSiteId, "os", query, { limit: 5, offset: 0 })}
          columns={[
            { header: "OS", render: (r) => r.os || "—" },
            { header: "Visitors", className: "text-right", render: (r) => r.visitors.toLocaleString() },
          ]}
          getRowKey={(r) => r.os}
        />
        <PaginatedCardTable<BrowserItem>
          title="Browsers"
          queryKey={["browsers", selectedSiteId, query]}
          initialPath={buildStatsListUrl(selectedSiteId, "browsers", query, { limit: 5, offset: 0 })}
          columns={[
            { header: "Browser", render: (r) => r.browser || "—" },
            { header: "Visitors", className: "text-right", render: (r) => r.visitors.toLocaleString() },
          ]}
          getRowKey={(r) => r.browser}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <PaginatedCardTable<TopPage>
          title="Top Pages"
          queryKey={["top-pages", selectedSiteId, query]}
          initialPath={buildStatsListUrl(selectedSiteId, "top-pages", query, { limit: 5, offset: 0 })}
          columns={[
            { header: "URL", render: (r) => <span className="truncate">{r.url}</span> },
            { header: "Visitors", className: "text-right", render: (r) => r.visitors.toLocaleString() },
            { header: "Pageviews", className: "text-right", render: (r) => r.pageviews.toLocaleString() },
          ]}
          getRowKey={(r) => r.url}
        />
        <PaginatedCardTable<TopReferrer>
          title="Top Referrers"
          queryKey={["top-referrers", selectedSiteId, query]}
          initialPath={buildStatsListUrl(selectedSiteId, "top-referrers", query, { limit: 5, offset: 0 })}
          columns={[
            { header: "Source", render: (r) => <span className="truncate">{r.source}</span> },
            { header: "Medium", render: (r) => <span className="truncate">{r.medium}</span> },
            { header: "Visitors", className: "text-right", render: (r) => r.visitors.toLocaleString() },
          ]}
          getRowKey={(r) => `${r.source}-${r.medium}`}
        />
      </div>
    </div>
  );
}
