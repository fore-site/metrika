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
      <div className="dot-grid grid min-h-screen place-items-center bg-background">
        <div className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3 shadow-sm">
          <Spinner className="h-4 w-4" />
          <div className="text-sm text-textSecondary">Restoring session…</div>
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

