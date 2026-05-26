"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { AuthCard } from "@/components/auth/AuthCard";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { apiFetchRaw, getApiBaseUrl } from "@/lib/api";
import { toast } from "@/lib/toast";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
});
type FormValues = z.infer<typeof schema>;

export default function ForgotPasswordPage() {
  const [sent, setSent] = React.useState(false);
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { email: "" } });

  const onSubmit = form.handleSubmit(async (values) => {
    const baseUrl = getApiBaseUrl();
    await apiFetchRaw(`${baseUrl}/api/auth/password-reset/`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: values.email }),
    }).catch(() => null);
    setSent(true);
    toast.success("If that email exists, a reset link has been sent.");
  });

  return (
    <AuthCard
      title="Reset your password"
      subtitle="We’ll email you a link to reset your password. If the email exists, you’ll receive it shortly."
    >
      {sent ? (
        <div className="rounded-md border border-success/30 bg-success/5 px-3 py-3 text-sm text-success">
          Check your email for a reset link.
        </div>
      ) : (
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <Label htmlFor="email">Email</Label>
            <div className="mt-2">
              <Input id="email" type="email" autoComplete="email" {...form.register("email")} />
            </div>
            {form.formState.errors.email ? (
              <p className="mt-2 text-sm text-danger">{form.formState.errors.email.message}</p>
            ) : null}
          </div>
          <Button type="submit" className="w-full" loading={form.formState.isSubmitting}>
            Send Reset Link
          </Button>
        </form>
      )}
    </AuthCard>
  );
}
