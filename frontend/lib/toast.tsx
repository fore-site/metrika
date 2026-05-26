"use client";

import type * as React from "react";
import { toast as hotToast } from "react-hot-toast";
import { AlertTriangle, CheckCircle2, Info, X, XCircle } from "lucide-react";

type ToastType = "success" | "error" | "warning" | "info";

const typeStyles: Record<ToastType, { icon: React.ReactNode; border: string; bg: string; text: string }> = {
  success: {
    icon: <CheckCircle2 className="h-4 w-4 text-success" />,
    border: "border-success/30",
    bg: "bg-success/5",
    text: "text-textPrimary",
  },
  error: {
    icon: <XCircle className="h-4 w-4 text-danger" />,
    border: "border-danger/30",
    bg: "bg-danger/5",
    text: "text-textPrimary",
  },
  warning: {
    icon: <AlertTriangle className="h-4 w-4 text-warning" />,
    border: "border-warning/30",
    bg: "bg-warning/5",
    text: "text-textPrimary",
  },
  info: {
    icon: <Info className="h-4 w-4 text-primary" />,
    border: "border-primary/30",
    bg: "bg-primary/5",
    text: "text-textPrimary",
  },
};

function show(type: ToastType, message: string, opts?: { duration?: number; dismissible?: boolean }) {
  const duration = opts?.duration ?? 5000;
  const dismissible = opts?.dismissible ?? true;
  const styles = typeStyles[type];

  return hotToast.custom(
    (toastItem) => (
      <div
        role="status"
        aria-live="polite"
        className={[
          "pointer-events-auto w-[360px] max-w-[calc(100vw-2rem)] rounded-xl border bg-white p-3 shadow-sm",
          styles.border,
          toastItem.visible ? "opacity-100" : "opacity-0",
        ].join(" ")}
      >
        <div className="flex items-start gap-3 font-body text-sm">
          <div className="mt-0.5">{styles.icon}</div>
          <div className={`flex-1 ${styles.text}`}>{message}</div>
          {dismissible ? (
            <button
              type="button"
              className="rounded-md p-1 text-textSecondary hover:bg-gray-100 hover:text-textPrimary"
              onClick={() => hotToast.dismiss(toastItem.id)}
              aria-label="Dismiss notification"
            >
              <X className="h-4 w-4" />
            </button>
          ) : null}
        </div>
        <div className={`mt-2 h-1 rounded-full ${styles.bg}`} />
      </div>
    ),
    { duration },
  );
}

export const toast = {
  success: (message: string, opts?: { duration?: number }) => show("success", message, opts),
  error: (message: string, opts?: { duration?: number }) => show("error", message, opts),
  warning: (message: string, opts?: { duration?: number }) => show("warning", message, opts),
  info: (message: string, opts?: { duration?: number }) => show("info", message, opts),
  dismiss: (id?: string) => hotToast.dismiss(id),
};

export function useToast() {
  return toast;
}

