export type ApiErrorItem = {
  code?: string;
  detail?: string;
  source?: { pointer?: string };
};

export type ApiEnvelope<T> =
  | { status: "success"; data: T; message?: string; meta?: Record<string, unknown> }
  | { status: "error"; data?: T; message?: string; errors?: ApiErrorItem[]; meta?: Record<string, unknown> };

export type PaginatedMeta = {
  total?: number;
  limit?: number;
  offset?: number;
  next?: string | null;
  previous?: string | null;
};

