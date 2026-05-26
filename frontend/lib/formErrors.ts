import type { FieldValues, UseFormSetError } from "react-hook-form";
import { ApiError } from "@/lib/errors";

export function applyApiFieldErrors<TFieldValues extends FieldValues>(
  err: unknown,
  setError: UseFormSetError<TFieldValues>,
) {
  if (!(err instanceof ApiError)) return false;
  const entries = Object.entries(err.fieldErrors ?? {});
  if (entries.length === 0) return false;
  for (const [field, message] of entries) {
    setError(field as never, { type: "server", message } as never);
  }
  return true;
}

