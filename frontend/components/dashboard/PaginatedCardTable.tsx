"use client";

import type * as React from "react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { usePaginatedQuery } from "@/lib/usePaginatedQuery";
import { ApiError } from "@/lib/errors";

export function PaginatedCardTable<T>(props: {
  title: string;
  subtitle?: string;
  queryKey: unknown[];
  initialPath: string;
  columns: { header: string; className?: string; render: (row: T) => React.ReactNode }[];
  getRowKey?: (row: T, idx: number) => string;
}) {
  const q = usePaginatedQuery<T>({ queryKey: props.queryKey, initialPath: props.initialPath });
  const rows = q.data?.pages.flatMap((p) => (p.status === "success" ? p.data : [])) ?? [];
  const errorText = q.error instanceof ApiError ? q.error.message : q.error ? "Unable to load data." : null;

  return (
    <Card className="p-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-base font-semibold">{props.title}</div>
          {props.subtitle ? <div className="mt-1 text-sm text-textSecondary">{props.subtitle}</div> : null}
        </div>
      </div>

      <div className="mt-5">
        {q.isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
          </div>
        ) : errorText ? (
          <div className="rounded-xl border border-danger/30 bg-danger/5 px-3 py-3 text-sm text-danger">
            {errorText}
          </div>
        ) : rows.length === 0 ? (
          <EmptyState title="No data yet" description="Once traffic comes in, it will show up here." />
        ) : (
          <div className="overflow-hidden rounded-xl border border-gray-200">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs text-textSecondary">
                <tr>
                  {props.columns.map((c) => (
                    <th key={c.header} className={`px-4 py-3 text-left font-medium ${c.className ?? ""}`}>
                      {c.header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {rows.map((row, idx) => (
                  <tr key={props.getRowKey ? props.getRowKey(row, idx) : String(idx)} className="hover:bg-gray-50/60">
                    {props.columns.map((c) => (
                      <td key={c.header} className={`px-4 py-3 ${c.className ?? ""}`}>
                        {c.render(row)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {q.hasNextPage ? (
        <div className="mt-4">
          <Button
            variant="secondary"
            className="w-full"
            onClick={() => q.fetchNextPage()}
            loading={q.isFetchingNextPage}
            type="button"
          >
            Load More
          </Button>
        </div>
      ) : null}
    </Card>
  );
}

