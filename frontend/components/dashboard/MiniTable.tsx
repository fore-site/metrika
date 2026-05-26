"use client";

import type * as React from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";

export function MiniTable<T>(props: {
  title: string;
  subtitle?: string;
  viewAllHref?: string;
  isLoading: boolean;
  error?: string | null;
  rows?: T[];
  columns: { header: string; className?: string; render: (row: T) => React.ReactNode }[];
  emptyTitle?: string;
  emptyDescription?: string;
}) {
  return (
    <Card className="p-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-base font-semibold">{props.title}</div>
          {props.subtitle ? <div className="mt-1 text-sm text-textSecondary">{props.subtitle}</div> : null}
        </div>
        {props.viewAllHref ? (
          <Link href={props.viewAllHref} className="text-sm font-medium text-primary hover:underline">
            View All
          </Link>
        ) : null}
      </div>

      <div className="mt-5">
        {props.isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
          </div>
        ) : props.error ? (
          <div className="rounded-xl border border-danger/30 bg-danger/5 px-3 py-3 text-sm text-danger">
            {props.error}
          </div>
        ) : (props.rows?.length ?? 0) === 0 ? (
          <EmptyState
            title={props.emptyTitle ?? "No data yet"}
            description={props.emptyDescription ?? "Once traffic comes in, it will show up here."}
          />
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
                {props.rows?.map((row, idx) => (
                  <tr key={idx} className="hover:bg-gray-50/60">
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
    </Card>
  );
}
