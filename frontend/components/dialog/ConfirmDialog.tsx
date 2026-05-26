"use client";

import * as React from "react";
import { createPortal } from "react-dom";
import { Button } from "@/components/ui/Button";

export function ConfirmDialog(props: {
  isOpen: boolean;
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: "danger" | "primary";
  onConfirm: () => void | Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}) {
  const { isOpen, onCancel } = props;
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  React.useEffect(() => {
    if (!isOpen) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [isOpen, onCancel]);

  if (!mounted || !isOpen) return null;
  const confirmVariant = props.variant === "danger" ? "danger" : "primary";

  return createPortal(
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-black/50 px-4"
      role="dialog"
      aria-modal="true"
      aria-label={props.title ?? "Are you sure?"}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) props.onCancel();
      }}
    >
      <div className="w-full max-w-md rounded-xl border border-gray-200 bg-white p-6 shadow-lg">
        <div className="font-heading text-xl font-semibold text-primary">{props.title ?? "Are you sure?"}</div>
        <div className="mt-2 text-sm text-textSecondary">{props.message}</div>
        <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-end">
          <Button variant="secondary" onClick={props.onCancel} type="button" disabled={props.loading}>
            {props.cancelText ?? "Cancel"}
          </Button>
          <Button variant={confirmVariant} onClick={props.onConfirm} type="button" loading={props.loading}>
            {props.confirmText ?? "Confirm"}
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
