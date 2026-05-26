import * as React from "react";
import { clsx } from "clsx";

export function EmptyState(props: { title: string; description?: string; className?: string; children?: React.ReactNode }) {
  return (
    <div className={clsx("dot-grid rounded-xl border border-gray-200 bg-white p-8 text-center", props.className)}>
      <div className="mx-auto max-w-md">
        <div className="text-base font-semibold text-textPrimary">{props.title}</div>
        {props.description ? <div className="mt-2 text-sm text-textSecondary">{props.description}</div> : null}
        {props.children ? <div className="mt-6 flex justify-center gap-3">{props.children}</div> : null}
      </div>
    </div>
  );
}

