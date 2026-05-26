"use client";

import * as React from "react";
import { apiFetch, apiFetchEnvelope } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export function useApi() {
  const auth = useAuth();
  return React.useMemo(
    () => ({
      get: <T,>(path: string) => apiFetch<T>(auth, path),
      post: <T,>(path: string, body?: unknown) =>
        apiFetch<T>(auth, path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
      put: <T,>(path: string, body?: unknown) =>
        apiFetch<T>(auth, path, { method: "PUT", body: body ? JSON.stringify(body) : undefined }),
      patch: <T,>(path: string, body?: unknown) =>
        apiFetch<T>(auth, path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
      del: <T,>(path: string) => apiFetch<T>(auth, path, { method: "DELETE" }),
      envelope: <T,>(path: string, init?: RequestInit) => apiFetchEnvelope<T>(auth, path, init),
    }),
    [auth],
  );
}

