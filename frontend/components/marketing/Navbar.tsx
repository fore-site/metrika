"use client";

import { Logo } from "@/components/branding/Logo";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/context/AuthContext";

export function MarketingNavbar() {
  const { accessToken } = useAuth();
  const isAuthenticated = !!accessToken;

  return (
    <header className="sticky top-0 z-30 border-b border-gray-200/70 bg-white/70 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <Logo />
        <nav className="hidden items-center gap-6 text-sm text-textSecondary md:flex">
          <a className="hover:text-textPrimary" href="/pricing">
            Pricing
          </a>
          <a className="hover:text-textPrimary" href="/docs">
            Docs
          </a>
        </nav>
        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <a href="/dashboard">
              <Button variant="secondary">Dashboard</Button>
            </a>
          ) : (
            <a href="/login">
              <Button variant="secondary">Sign In</Button>
            </a>
          )}
        </div>
      </div>
    </header>
  );
}