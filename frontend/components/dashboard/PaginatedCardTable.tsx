"use client";

import * as React from "react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { Modal } from "@/components/ui/Modal";
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
  const [modalOpen, setModalOpen] = React.useState(false);

  // Preview query (first 5 items)
  const preview = usePaginatedQuery<T>({
    queryKey: props.queryKey,
    initialPath: `${props.initialPath}?limit=10&offset=0`,
  });
  const previewRows =
    preview.data?.pages.flatMap((p) => (p.status === "success" ? p.data : [])) ?? [];
  const previewError =
    preview.error instanceof ApiError
      ? preview.error.message
      : preview.error
      ? "Unable to load data."
      : null;

  // Modal query – starts with 20 items, fetches more on "Load More"
  const modalQuery = usePaginatedQuery<T>({
    queryKey: [...props.queryKey, "modal"],
    initialPath: `${props.initialPath}?limit=20&offset=0`,
    enabled: modalOpen,
  });
  const modalRows =
    modalQuery.data?.pages.flatMap((p) => (p.status === "success" ? p.data : [])) ?? [];
  const modalError =
    modalQuery.error instanceof ApiError
      ? modalQuery.error.message
      : modalQuery.error
      ? "Unable to load data."
      : null;

  return (
    <Card className="p-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-base font-semibold">{props.title}</div>
          {props.subtitle ? (
            <div className="mt-1 text-sm text-textSecondary">{props.subtitle}</div>
          ) : null}
        </div>
        {previewRows.length > 0 && (
          <Button variant="secondary" type="button" onClick={() => setModalOpen(true)}>
            View All
          </Button>
        )}
      </div>

      {/* Preview table */}
      <div className="mt-5">
        {preview.isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
          </div>
        ) : previewError ? (
          <div className="rounded-xl border border-danger/30 bg-danger/5 px-3 py-3 text-sm text-danger">
            {previewError}
          </div>
        ) : previewRows.length === 0 ? (
          <EmptyState title="No data yet" description="Once traffic comes in, it will show up here." />
        ) : (
          <div className="overflow-x-auto rounded-xl border border-gray-200">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs text-textSecondary">
                <tr>
                  {props.columns.map((c) => (
                    <th
                      key={c.header}
                      className={`px-4 py-3 text-left font-medium ${c.className ?? ""}`}
                    >
                      {c.header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {previewRows.map((row, idx) => (
                  <tr
                    key={props.getRowKey ? props.getRowKey(row, idx) : String(idx)}
                    className="hover:bg-gray-50/60"
                  >
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

      {/* Modal with Load More */}
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={props.title}>
        {modalQuery.isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
          </div>
        ) : modalError ? (
          <div className="text-sm text-danger">{modalError}</div>
        ) : modalRows.length === 0 ? (
          <EmptyState title="No data" description="Nothing to show." />
        ) : (
          <>
            <div className="overflow-x-auto rounded-xl border border-gray-200">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-xs text-textSecondary">
                  <tr>
                    {props.columns.map((c) => (
                      <th
                        key={c.header}
                        className={`px-4 py-3 text-left font-medium ${c.className ?? ""}`}
                      >
                        {c.header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {modalRows.map((row, idx) => (
                    <tr
                      key={props.getRowKey ? props.getRowKey(row, idx) : String(idx)}
                      className="hover:bg-gray-50/60"
                    >
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

            {modalQuery.hasNextPage && (
              <div className="mt-4">
                <Button
                  variant="secondary"
                  className="w-full"
                  onClick={() => modalQuery.fetchNextPage()}
                  loading={modalQuery.isFetchingNextPage}
                  type="button"
                >
                  Load More
                </Button>
              </div>
            )}
          </>
        )}
      </Modal>
    </Card>
  );
}