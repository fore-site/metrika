"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Settings, UserCircle2, LogOut, Menu, X } from "lucide-react";
import { Logo } from "@/components/branding/Logo";
import { Button } from "@/components/ui/Button";
import { useApi } from "@/lib/useApi";
import { setSearchParams } from "@/lib/url";
import type { Site } from "@/types/site";
import { DateRangePicker } from "@/components/dashboard/DateRangePicker";

export function TopNav() {
  const api = useApi();
  const pathname = usePathname();
  const router = useRouter();
  const sp = useSearchParams();
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [menuOpen, setMenuOpen] = React.useState(false);

  const sitesQuery = useQuery({
    queryKey: ["sites"],
    queryFn: () => api.get<Site[]>("/api/sites/"),
  });

  const siteId = sp.get("site") || "";
  const sites = sitesQuery.data ?? [];
  const selectedSite = sites.find((s) => String(s.id) === siteId) ?? sites[0] ?? null;

  React.useEffect(() => {
    if (!sitesQuery.isSuccess) return;
    if (!selectedSite) return;
    if (siteId) return;
    const next = setSearchParams(sp as unknown as URLSearchParams, { site: String(selectedSite.id) });
    router.replace(`${pathname}?${next.toString()}`);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sitesQuery.isSuccess, selectedSite?.id]);

  const setSite = (id: string) => {
    const next = setSearchParams(sp as unknown as URLSearchParams, { site: id });
    router.replace(`${pathname}?${next.toString()}`);
  };

  const showDatePicker = pathname.startsWith("/dashboard");

  return (
    <header className="sticky top-0 z-30 border-b border-gray-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-4 sm:px-6">
        <div className="flex items-center gap-3">
          <button
            className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-gray-200 bg-white text-textPrimary md:hidden"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
          <Logo href="/dashboard" />
        </div>

        <div className="hidden flex-1 items-center justify-center gap-3 md:flex">
          <div className="w-full max-w-md">
            <label className="sr-only" htmlFor="site">
              Site
            </label>
            <select
              id="site"
              className="input h-11"
              value={selectedSite ? String(selectedSite.id) : ""}
              onChange={(e) => setSite(e.target.value)}
              disabled={sitesQuery.isLoading || sites.length === 0}
            >
              {sites.length === 0 ? <option value="">No sites</option> : null}
              {sites.map((s) => (
                <option key={s.id} value={String(s.id)}>
                  {s.domain}
                </option>
              ))}
            </select>
          </div>
          {showDatePicker ? <DateRangePicker /> : null}
        </div>

        <div className="flex items-center gap-2">
          <Link
            href={selectedSite ? `/sites/${selectedSite.id}` : "/dashboard"}
            className="hidden md:inline-flex"
            aria-label="Site settings"
          >
            <Button variant="secondary">
              <Settings className="h-4 w-4" />
              Settings
            </Button>
          </Link>

          <div className="relative">
            <button
              className="inline-flex h-11 items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 text-textPrimary hover:bg-gray-50"
              onClick={() => setMenuOpen((v) => !v)}
              aria-label="Account menu"
            >
              <UserCircle2 className="h-6 w-6 text-textSecondary" />
              <span className="hidden text-sm font-medium md:block">Account</span>
            </button>
            {menuOpen ? (
              <div className="absolute right-0 mt-2 w-52 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
                <Link
                  className="flex items-center gap-2 px-4 py-3 text-sm hover:bg-gray-50"
                  href="/profile"
                  onClick={() => setMenuOpen(false)}
                >
                  <UserCircle2 className="h-4 w-4 text-textSecondary" />
                  Profile
                </Link>
                <Link
                  className="flex items-center gap-2 px-4 py-3 text-sm hover:bg-gray-50"
                  href="/logout"
                  onClick={() => setMenuOpen(false)}
                >
                  <LogOut className="h-4 w-4 text-textSecondary" />
                  Logout
                </Link>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {mobileOpen ? (
        <div className="border-t border-gray-200 bg-white px-4 pb-4 pt-4 md:hidden">
          <div className="space-y-3">
            <div>
              <div className="text-xs font-medium text-textSecondary">Site</div>
              <select
                className="input mt-2 h-11"
                value={selectedSite ? String(selectedSite.id) : ""}
                onChange={(e) => setSite(e.target.value)}
                disabled={sitesQuery.isLoading || sites.length === 0}
              >
                {sites.length === 0 ? <option value="">No sites</option> : null}
                {sites.map((s) => (
                  <option key={s.id} value={String(s.id)}>
                    {s.domain}
                  </option>
                ))}
              </select>
            </div>
            {showDatePicker ? <DateRangePicker /> : null}
            <div className="flex gap-2">
              <Link href={selectedSite ? `/sites/${selectedSite.id}` : "/dashboard"} className="flex-1">
                <Button variant="secondary" className="w-full">
                  <Settings className="h-4 w-4" /> Settings
                </Button>
              </Link>
              <Link href="/profile" className="flex-1">
                <Button variant="secondary" className="w-full">
                  <UserCircle2 className="h-4 w-4" /> Profile
                </Button>
              </Link>
            </div>
          </div>
        </div>
      ) : null}
    </header>
  );
}

