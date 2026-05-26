"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { useApi } from "@/lib/useApi";
import type { ApiEnvelope, PaginatedMeta } from "@/lib/types";

type PaginatedEnvelope<T> = ApiEnvelope<T[]> & { meta?: PaginatedMeta };

export function usePaginatedQuery<T>(opts: { queryKey: unknown[]; initialPath: string; enabled?: boolean }) {
  const api = useApi();

  return useInfiniteQuery({
    queryKey: opts.queryKey,
    enabled: opts.enabled ?? true,
    initialPageParam: opts.initialPath,
    queryFn: async ({ pageParam }) => {
      const env = await api.envelope<T[]>(String(pageParam));
      return env as PaginatedEnvelope<T>;
    },
    getNextPageParam: (lastPage) => {
      if (lastPage.status !== "success") return undefined;
      const next = (lastPage as PaginatedEnvelope<T>).meta?.next ?? null;
      return next || undefined;
    },
  });
}

