"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { apiFetchRaw, getApiBaseUrl, getCsrfToken } from "@/lib/api";
import { normalizeApiError } from "@/lib/errors";
import type { ApiEnvelope } from "@/lib/types";
import { toast } from "@/lib/toast";

type LoginResponse = ApiEnvelope<{ access: string }>;

type AuthContextValue = {
  accessToken: string | null;
  isBootstrapping: boolean;
  setAccessToken: (token: string | null) => void;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<string | null>;
};

const AuthContext = React.createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [accessToken, setAccessToken] = React.useState<string | null>(null);
  const [isBootstrapping, setIsBootstrapping] = React.useState(true);

  const refreshAccessToken = React.useCallback(async (): Promise<string | null> => {
    const baseUrl = getApiBaseUrl();
    const csrf = getCsrfToken();
    const res = await apiFetchRaw(`${baseUrl}/api/auth/token/refresh/`, {
      method: "POST",
      credentials: "include",
      headers: csrf ? { "X-CSRFToken": csrf } : undefined,
    });
    if (!res.ok) {
      setAccessToken(null);
      return null;
    }
    const body = (await res.json()) as ApiEnvelope<{ access: string }>;
    if (body.status !== "success" || !body.data?.access) {
      setAccessToken(null);
      return null;
    }
    setAccessToken(body.data.access);
    return body.data.access;
  }, []);

  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await refreshAccessToken();
      } catch {
        // ignore
      } finally {
        if (!cancelled) setIsBootstrapping(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [refreshAccessToken]);

  const login = React.useCallback(
    async (email: string, password: string) => {
      const baseUrl = getApiBaseUrl();
      const res = await apiFetchRaw(`${baseUrl}/api/auth/login/`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const json = (await res.json().catch(() => null)) as LoginResponse | null;
      if (!res.ok || !json || json.status !== "success" || !json.data?.access) {
        if (res.status === 429) toast.warning("Too many requests. Please wait a moment.");
        if (res.status >= 500) toast.error("Something went wrong on the server. Please try again.");
        throw normalizeApiError(res.status, json);
      }
      setAccessToken(json.data.access);
      toast.success("Signed in successfully.");
      router.push("/dashboard");
    },
    [router],
  );

  const logout = React.useCallback(async () => {
    const baseUrl = getApiBaseUrl();
    const csrf = getCsrfToken();
    const res = await apiFetchRaw(`${baseUrl}/api/auth/logout/`, {
      method: "POST",
      credentials: "include",
      headers: {
        ...(csrf ? { "X-CSRFToken": csrf } : {}),
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
    });
    if (!res.ok) {
      setAccessToken(null);
      toast.info("Signed out.");
      router.push("/login");
      return;
    }
    setAccessToken(null);
    toast.info("Signed out.");
    router.push("/login");
  }, [accessToken, router]);

  const value = React.useMemo<AuthContextValue>(
    () => ({
      accessToken,
      isBootstrapping,
      setAccessToken,
      login,
      logout,
      refreshAccessToken,
    }),
    [accessToken, isBootstrapping, login, logout, refreshAccessToken],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function useRequireAuth() {
  const router = useRouter();
  const { accessToken, isBootstrapping } = useAuth();

  React.useEffect(() => {
    if (!isBootstrapping && !accessToken) router.replace("/login");
  }, [accessToken, isBootstrapping, router]);

  return { accessToken, isBootstrapping };
}
