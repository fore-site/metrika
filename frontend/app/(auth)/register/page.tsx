"use client";

import Link from "next/link";
import * as React from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { AuthCard } from "@/components/auth/AuthCard";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { apiFetchRaw, getApiBaseUrl } from "@/lib/api";
import { applyApiFieldErrors } from "@/lib/formErrors";
import { ApiError, normalizeApiError } from "@/lib/errors";
import type { ApiEnvelope } from "@/lib/types";
import { toast } from "@/lib/toast";

const passwordRules = z
  .string()
  .min(8, "At least 8 characters")
  .regex(/[A-Z]/, "Include an uppercase letter")
  .regex(/[0-9]/, "Include a number")
  .regex(/[^A-Za-z0-9]/, "Include a special character");

const schema = z
  .object({
    name: z.string().min(2, "Name is required"),
    email: z.string().email("Enter a valid email"),
    password: passwordRules,
    confirmPassword: z.string().min(1, "Confirm your password"),
  })
  .refine((v) => v.password === v.confirmPassword, { message: "Passwords do not match", path: ["confirmPassword"] });

type FormValues = z.infer<typeof schema>;

export default function RegisterPage() {
  const router = useRouter();
  const [serverError, setServerError] = React.useState<string | null>(null);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", email: "", password: "", confirmPassword: "" },
  });

  const onSubmit = form.handleSubmit(async (values) => {
    setServerError(null);
    const baseUrl = getApiBaseUrl();
    const res = await apiFetchRaw(`${baseUrl}/api/auth/register/`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: values.name, email: values.email, password: values.password }),
    });

    const json = (await res.json().catch(() => null)) as ApiEnvelope<Record<string, never>> | null;
    if (!res.ok || !json || json.status !== "success") {
      const err = normalizeApiError(res.status, json);
      if (res.status === 429) toast.warning("Too many requests. Please wait a moment.");
      if (res.status >= 500) toast.error("Something went wrong on the server. Please try again.");
      const applied = applyApiFieldErrors(err, form.setError);
      if (!applied) setServerError(err instanceof ApiError ? err.message : "Unable to register.");
      return;
    }

    toast.success("Account created. Check your email to verify it.");
    router.push(`/verify-email?email=${encodeURIComponent(values.email)}`);
  });

  return (
    <AuthCard title="Create your account" subtitle="Start tracking in minutes. No invasive tracking required.">
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <Label htmlFor="name">Name</Label>
          <div className="mt-2">
            <Input id="name" autoComplete="name" {...form.register("name")} />
          </div>
          {form.formState.errors.name ? (
            <p className="mt-2 text-sm text-danger">{form.formState.errors.name.message}</p>
          ) : null}
        </div>

        <div>
          <Label htmlFor="email">Email</Label>
          <div className="mt-2">
            <Input id="email" type="email" autoComplete="email" {...form.register("email")} />
          </div>
          {form.formState.errors.email ? (
            <p className="mt-2 text-sm text-danger">{form.formState.errors.email.message}</p>
          ) : null}
        </div>

        <div>
          <Label htmlFor="password">Password</Label>
          <div className="mt-2">
            <Input id="password" type="password" autoComplete="new-password" {...form.register("password")} />
          </div>
          {form.formState.errors.password ? (
            <p className="mt-2 text-sm text-danger">{form.formState.errors.password.message}</p>
          ) : (
            <p className="mt-2 text-xs text-textSecondary">
              8+ chars, uppercase, number, and special character.
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="confirmPassword">Confirm password</Label>
          <div className="mt-2">
            <Input id="confirmPassword" type="password" autoComplete="new-password" {...form.register("confirmPassword")} />
          </div>
          {form.formState.errors.confirmPassword ? (
            <p className="mt-2 text-sm text-danger">{form.formState.errors.confirmPassword.message}</p>
          ) : null}
        </div>

        {serverError ? (
          <div className="rounded-md border border-danger/30 bg-danger/5 px-3 py-2 text-sm text-danger">
            {serverError}
          </div>
        ) : null}

        <Button type="submit" className="w-full" loading={form.formState.isSubmitting}>
          Create account
        </Button>

        <div className="text-center text-sm text-textSecondary">
          Already have an account?{" "}
          <Link href="/login" className="text-primary hover:underline">
            Sign in
          </Link>
        </div>
      </form>
    </AuthCard>
  );
}
