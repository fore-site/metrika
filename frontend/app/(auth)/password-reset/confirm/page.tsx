"use client";

import Link from "next/link";
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
import { Suspense } from "react";
import type { ApiEnvelope } from "@/lib/types";

const passwordRules = z
  .string()
  .min(8, "At least 8 characters")
  .regex(/[A-Z]/, "Include an uppercase letter")
  .regex(/[0-9]/, "Include a number")
  .regex(/[^A-Za-z0-9]/, "Include a special character");

const schema = z
  .object({
    newPassword: passwordRules,
    confirmPassword: z.string().min(1, "Confirm your password"),
  })
  .refine((v) => v.newPassword === v.confirmPassword, { message: "Passwords do not match", path: ["confirmPassword"] });

type FormValues = z.infer<typeof schema>;

function PasswordResetConfirm() {
  const sp = useSearchParams();
  const uid = sp.get("uid");
  const token = sp.get("token");
  const [done, setDone] = React.useState(false);
  const [serverError, setServerError] = React.useState<string | null>(null);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { newPassword: "", confirmPassword: "" },
  });

  const onSubmit = form.handleSubmit(async (values) => {
    setServerError(null);
    if (!uid || !token) {
      setServerError("Invalid reset link. Please request a new one.");
      return;
    }
    const baseUrl = getApiBaseUrl();
    const res = await apiFetchRaw(`${baseUrl}/api/auth/password-reset/confirm/`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: uid, token, new_password: values.newPassword }),
    });
    const json = (await res.json().catch(() => null)) as ApiEnvelope<Record<string, never>> | null;
    if (res.ok && json?.status === "success") {
      setDone(true);
    } else {
      const message = json?.message ?? "Invalid or expired reset token.";
      setServerError(message);
    }
  });

  return (
    <AuthCard title="Set a new password" subtitle="Choose a strong password you haven’t used before.">
      {done ? (
        <div className="space-y-4">
          <div className="rounded-md border border-success/30 bg-success/5 px-3 py-3 text-sm text-success">
            Password reset successful. You can now sign in.
          </div>
          <a href="/login" className="inline-flex w-full">
            <Button className="w-full">Go to Login</Button>
          </a>
        </div>
      ) : (
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <Label htmlFor="newPassword">New password</Label>
            <div className="mt-2">
              <Input id="newPassword" type="password" autoComplete="new-password" {...form.register("newPassword")} />
            </div>
            {form.formState.errors.newPassword ? (
              <p className="mt-2 text-sm text-danger">{form.formState.errors.newPassword.message}</p>
            ) : null}
          </div>
          <div>
            <Label htmlFor="confirmPassword">Confirm password</Label>
            <div className="mt-2">
              <Input
                id="confirmPassword"
                type="password"
                autoComplete="new-password"
                {...form.register("confirmPassword")}
              />
            </div>
            {form.formState.errors.confirmPassword ? (
              <p className="mt-2 text-sm text-danger">{form.formState.errors.confirmPassword.message}</p>
            ) : null}
          </div>

          {serverError ? (
            <div className="rounded-md border border-danger/30 bg-danger/5 px-3 py-3 text-sm text-danger">
              {serverError}{" "}
              <a href="/forgot-password" className="underline">
                Request a new reset link
              </a>
              .
            </div>
          ) : null}

          <Button type="submit" className="w-full" loading={form.formState.isSubmitting}>
            Reset Password
          </Button>
        </form>
      )}
    </AuthCard>
  );
}

export default function PasswordResetConfirmPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background" />}>
      <PasswordResetConfirm />
    </Suspense>
  );
}