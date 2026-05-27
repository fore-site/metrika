import { ApiError, normalizeApiError } from "@/lib/errors";
import type { ApiEnvelope } from "@/lib/types";
import { toast } from "@/lib/toast";

const DEFAULT_API_URL = "https://metrika-api.up.railway.app";

export function getApiBaseUrl() {
  return (process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_URL).replace(/\/+$/, "");
}

export function getCookie(name: string) {
  if (typeof document === "undefined") return null;
  const m = document.cookie.match(new RegExp(`(?:^|; )${name.replace(/[.$?*|{}()[\]\\/+^]/g, "\\$&")}=([^;]*)`));
  return m ? decodeURIComponent(m[1]) : null;
}

export function getCsrfToken() {
  return getCookie("csrftoken");
}

export async function apiFetchRaw(input: RequestInfo | URL, init?: RequestInit) {
  return fetch(input, init);
}

function isUnsafeMethod(method?: string) {
  const m = (method ?? "GET").toUpperCase();
  return ["POST", "PUT", "PATCH", "DELETE"].includes(m);
}

type AuthLike = {
  accessToken: string | null;
  setAccessToken: (token: string | null) => void;
  refreshAccessToken: () => Promise<string | null>;
};

function notifyApiError(status: number) {
  if (typeof window === "undefined") return;
  if (status === 429) toast.warning("Too many requests. Please wait a moment.");
  if (status >= 500) toast.error("Something went wrong on the server. Please try again.");
}

function redirectToLogin() {
  if (typeof window === "undefined") return;
  if (window.location.pathname === "/login") return;
  const next = `${window.location.pathname}${window.location.search}`;
  window.location.assign(`/login?next=${encodeURIComponent(next)}`);
}

export async function apiFetch<T>(
  auth: AuthLike,
  pathOrUrl: string,
  init: RequestInit = {},
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const url = pathOrUrl.startsWith("http") ? pathOrUrl : `${baseUrl}${pathOrUrl.startsWith("/") ? "" : "/"}${pathOrUrl}`;

  const method = (init.method ?? "GET").toUpperCase();
  const csrf = isUnsafeMethod(method) ? getCsrfToken() : null;

  const headers = new Headers(init.headers ?? {});
  headers.set("Accept", "application/json");
  if (!headers.has("Content-Type") && init.body) headers.set("Content-Type", "application/json");
  if (auth.accessToken) headers.set("Authorization", `Bearer ${auth.accessToken}`);
  if (csrf) headers.set("X-CSRFToken", csrf);

  const doRequest = async () =>
    apiFetchRaw(url, {
      ...init,
      method,
      headers,
      credentials: "include",
    });

  let res = await doRequest();

  if (res.status === 401) {
    const nextToken = await auth.refreshAccessToken().catch(() => null);
    if (nextToken) {
      auth.setAccessToken(nextToken);
      headers.set("Authorization", `Bearer ${nextToken}`);
      res = await doRequest();
    } else {
      auth.setAccessToken(null);
      redirectToLogin();
    }
  }

  const json = (await res.json().catch(() => null)) as ApiEnvelope<T> | null;
  if (!res.ok || !json || json.status !== "success") {
    notifyApiError(res.status);
    throw normalizeApiError(res.status, json);
  }
  return json.data;
}

export async function apiFetchEnvelope<T>(auth: AuthLike, pathOrUrl: string, init: RequestInit = {}) {
  const baseUrl = getApiBaseUrl();
  const url = pathOrUrl.startsWith("http") ? pathOrUrl : `${baseUrl}${pathOrUrl.startsWith("/") ? "" : "/"}${pathOrUrl}`;

  const method = (init.method ?? "GET").toUpperCase();
  const csrf = isUnsafeMethod(method) ? getCsrfToken() : null;

  const headers = new Headers(init.headers ?? {});
  headers.set("Accept", "application/json");
  if (!headers.has("Content-Type") && init.body) headers.set("Content-Type", "application/json");
  if (auth.accessToken) headers.set("Authorization", `Bearer ${auth.accessToken}`);
  if (csrf) headers.set("X-CSRFToken", csrf);

  const doRequest = async () =>
    apiFetchRaw(url, {
      ...init,
      method,
      headers,
      credentials: "include",
    });

  let res = await doRequest();

  if (res.status === 401) {
    const nextToken = await auth.refreshAccessToken().catch(() => null);
    if (nextToken) {
      auth.setAccessToken(nextToken);
      headers.set("Authorization", `Bearer ${nextToken}`);
      res = await doRequest();
    } else {
      auth.setAccessToken(null);
      redirectToLogin();
    }
  }

  const json = (await res.json().catch(() => null)) as ApiEnvelope<T> | null;

  if (!res.ok || !json || json.status !== "success") {
    notifyApiError(res.status);
    if (json) throw normalizeApiError(res.status, json);
    throw new ApiError(res.status, "Request failed");
  }
  return json;
}
