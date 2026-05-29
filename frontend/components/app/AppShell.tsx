"use client";

import * as React from "react";
import { TopNav } from "@/components/app/TopNav";
import { useRequireAuth } from "@/context/AuthContext";
import { Spinner } from "@/components/ui/Button";
import { MarketingFooter } from "@/components/marketing/Footer";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { accessToken, isBootstrapping } = useRequireAuth();

  if (isBootstrapping) {
    return (
      <div className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6">
        {/* Stats row – six cards */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-xl" />
          ))}
        </div>
        {/* Timeseries chart placeholder */}
        <Skeleton className="h-80 w-full rounded-xl" />
        {/* Bottom grids (Top Pages / Referrers / Geography etc.) */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <Skeleton className="h-48 w-full rounded-xl" />
          <Skeleton className="h-48 w-full rounded-xl" />
          <Skeleton className="h-48 w-full rounded-xl" />
        </div>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Skeleton className="h-48 w-full rounded-xl" />
          <Skeleton className="h-48 w-full rounded-xl" />
        </div>
      </div>
    );
  }

  if (!accessToken) return null;

  return (
    <div className="min-h-screen bg-background">
      <TopNav />
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">{children}</main>
      <MarketingFooter />
    </div>
  );
}

