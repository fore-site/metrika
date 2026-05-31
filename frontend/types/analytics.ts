export type SummaryData = {
  visitors: number;
  pageviews: number;
  total_visits: number;
  bounce_rate: number;
  avg_duration_seconds: number;
  views_per_visit: number;
};

export type TimeseriesEntry = {
  day?: string;
  month?: string;
  year?: string;
  hour?: string;
  visitors: number;
  pageviews: number;
  total_visits: number;
  bounce_rate: number;
  avg_duration_seconds: number;
  views_per_visit: number;
};

export type TopPage = { url: string; visitors: number; pageviews: number };
export type TopReferrer = { source: string; medium: string; visitors: number; pageviews: number };
export type CountryItem = { country: string; visitors: number };
export type RegionItem = { region: string; visitors: number };
export type CityItem = { city: string; visitors: number };
export type DeviceItem = { device_type: string; visitors: number };
export type BrowserItem = { browser: string; visitors: number };
export type OSItem = { os: string; visitors: number };

