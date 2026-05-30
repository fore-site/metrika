"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { AuthCard } from "@/components/auth/AuthCard";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { useAuth } from "@/context/AuthContext";
import { applyApiFieldErrors } from "@/lib/formErrors";
import { ApiError } from "@/lib/errors";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const { login } = useAuth();
  const [serverError, setServerError] = React.useState<string | null>(null);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = form.handleSubmit(async (values) => {
    setServerError(null);
    try {
      await login(values.email, values.password);
    } catch (err) {
      const applied = applyApiFieldErrors(err, form.setError);
      if (!applied) setServerError(err instanceof ApiError ? err.message : "Unable to sign in.");
    }
  });

  return (
    <AuthCard title="Sign in" subtitle="Welcome back. Let’s get you into your dashboard.">
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

        <div>
          <Label htmlFor="password">Password</Label>
          <div className="mt-2">
            <Input id="password" type="password" autoComplete="current-password" {...form.register("password")} />
          </div>
          {form.formState.errors.password ? (
            <p className="mt-2 text-sm text-danger">{form.formState.errors.password.message}</p>
          ) : null}
        </div>

        {serverError ? (
          <div className="rounded-md border border-danger/30 bg-danger/5 px-3 py-2 text-sm text-danger">
            {serverError}
          </div>
        ) : null}

        <Button type="submit" className="w-full" loading={form.formState.isSubmitting}>
          Sign In
        </Button>

        <div className="flex items-center justify-between text-sm">
          <a href="/forgot-password" className="text-primary hover:underline">
            Forgot password?
          </a>
          <a href="/register" className="text-primary hover:underline">
            Create account
          </a>
        </div>
      </form>
    </AuthCard>
  );
}

