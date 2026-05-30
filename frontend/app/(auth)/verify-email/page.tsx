"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { AuthCard } from "@/components/auth/AuthCard";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { apiFetchRaw, getApiBaseUrl } from "@/lib/api";
import type { ApiEnvelope } from "@/lib/types";
import { toast } from "@/lib/toast";

const resendSchema = z.object({
  email: z.string().email("Enter a valid email"),
});
type ResendValues = z.infer<typeof resendSchema>;

function VerifyEmail() {
  const router = useRouter();
  const sp = useSearchParams();

  const userId = sp.get("user_id");
  const token = sp.get("token");
  const prefillEmail = sp.get("email") ?? "";

  const [verifying, setVerifying] = React.useState(Boolean(userId && token));
  const [verifyError, setVerifyError] = React.useState<string | null>(null);
  const [resent, setResent] = React.useState(false);

  const form = useForm<ResendValues>({
    resolver: zodResolver(resendSchema),
    defaultValues: { email: prefillEmail },
  });

  React.useEffect(() => {
    if (!userId || !token) return;
    let cancelled = false;
    (async () => {
      setVerifyError(null);
      setVerifying(true);
      const baseUrl = getApiBaseUrl();
      const res = await apiFetchRaw(`${baseUrl}/api/auth/verify-email/`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, token }),
      });
      const json = (await res.json().catch(() => null)) as ApiEnvelope<Record<string, never>> | null;
      if (!cancelled) {
        if (res.ok && json?.status === "success") {
          toast.success("Email verified.");
          router.replace("/verified");
        } else {
          setVerifyError(json?.message ?? "Invalid or expired verification link.");
        }
        setVerifying(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [router, token, userId]);

  const onResend = form.handleSubmit(async (values) => {
    setResent(false);
    const baseUrl = getApiBaseUrl();
    const res = await apiFetchRaw(`${baseUrl}/api/auth/resend-verification/`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: values.email }),
    });
    const json = (await res.json().catch(() => null)) as ApiEnvelope<Record<string, never>> | null;
    if (res.ok && json?.status === "success") {
      setResent(true);
    } else {
      const message = json?.message ?? "Unable to resend.";
      form.setError("email", { type: "server", message });
    }
  });

  return (
    <AuthCard
      title={verifying ? "Verifying your email..." : "Verify your email"}
      subtitle="Check your inbox for a verification link. If you don’t see it, check spam or request a new one."
    >
      {verifyError ? (
        <div className="mb-4 rounded-md border border-danger/30 bg-danger/5 px-3 py-3 text-sm text-danger">
          {verifyError}
        </div>
      ) : null}

      {verifying ? (
        <div className="rounded-md border border-gray-200 bg-white px-3 py-3 text-sm text-textSecondary">Working…</div>
      ) : (
        <form onSubmit={onResend} className="space-y-4">
          <div>
            <Label htmlFor="email">Email</Label>
            <div className="mt-2">
              <Input id="email" type="email" autoComplete="email" {...form.register("email")} />
            </div>
            {form.formState.errors.email ? (
              <p className="mt-2 text-sm text-danger">{form.formState.errors.email.message}</p>
            ) : null}
          </div>
          {resent ? (
            <div className="rounded-md border border-success/30 bg-success/5 px-3 py-3 text-sm text-success">
              A new verification link has been sent.
            </div>
          ) : null}
          <Button type="submit" className="w-full" loading={form.formState.isSubmitting}>
            Resend verification
          </Button>
        </form>
      )}
    </AuthCard>
  );
}

export default function VerifyEmailPage() {
  return (
    <React.Suspense fallback={<div className="min-h-screen bg-background" />}>
      <VerifyEmail />
    </React.Suspense>
  );
}