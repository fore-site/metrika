import type { ApiEnvelope, ApiErrorItem } from "@/lib/types";

export class ApiError extends Error {
  status: number;
  messageFromServer?: string;
  fieldErrors: Record<string, string>;

  constructor(status: number, message: string, fieldErrors: Record<string, string> = {}, messageFromServer?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fieldErrors = fieldErrors;
    this.messageFromServer = messageFromServer;
  }
}

function pointerToField(pointer?: string) {
  if (!pointer) return null;
  const parts = pointer.split("/").filter(Boolean);
  return parts.at(-1) ?? null;
}

export function extractFieldErrors(errors?: ApiErrorItem[]) {
  const out: Record<string, string> = {};
  for (const item of errors ?? []) {
    const field = pointerToField(item.source?.pointer);
    const msg = item.detail ?? item.code ?? "Invalid value";
    if (field) out[field] = msg;
  }
  return out;
}

export function normalizeApiError(status: number, body: ApiEnvelope<unknown> | null) {
  if (body?.status === "error") {

    const fieldErrors = extractFieldErrors(body.errors);
    const messageFromServer = body.message ?? "Request failed";
    return new ApiError(status, messageFromServer, fieldErrors, messageFromServer);
  }
  return new ApiError(status, "Request failed");
}

