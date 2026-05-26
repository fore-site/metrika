"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { ConfirmDialog } from "@/components/dialog/ConfirmDialog";
import { useApi } from "@/lib/useApi";
import { useAuth } from "@/context/AuthContext";
import { ApiError } from "@/lib/errors";
import { toast } from "@/lib/toast";

const schema = z.object({
  password: z.string().min(1, "Password is required"),
});

type FormValues = z.infer<typeof schema>;

export default function DeleteAccountPage() {
  const api = useApi();
  const router = useRouter();
  const { setAccessToken } = useAuth();
  const [isConfirmOpen, setIsConfirmOpen] = React.useState(false);
  const [isDeleting, setIsDeleting] = React.useState(false);
  const [serverError, setServerError] = React.useState<string | null>(null);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { password: "" },
  });

  const openConfirm = form.handleSubmit(() => {
    setServerError(null);
    setIsConfirmOpen(true);
  });

  const deleteAccount = async () => {
    setIsDeleting(true);
    setServerError(null);
    try {
      await api.post<Record<string, never>>("/api/auth/delete-account/", { password: form.getValues("password") });
      setAccessToken(null);
      toast.success("Your account has been deleted.");
      router.push("/");
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Unable to delete account.";
      setServerError(message.toLowerCase().includes("password") ? "Password is incorrect" : message);
      toast.error(message);
    } finally {
      setIsDeleting(false);
      setIsConfirmOpen(false);
    }
  };

  return (
    <div className="mx-auto max-w-md py-8">
      <Card className="p-6 sm:p-8">
        <div className="flex items-start gap-3">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-danger/10 text-danger">
            <AlertTriangle className="h-5 w-5" />
          </span>
          <div>
            <h1 className="font-heading text-2xl font-semibold text-primary">Delete your account</h1>
            <p className="mt-2 text-sm leading-6 text-textSecondary">
              This action is permanent and cannot be undone. All your data, sites, and analytics will be deleted.
            </p>
          </div>
        </div>

        <form onSubmit={openConfirm} className="mt-6 space-y-4">
          <div>
            <Label htmlFor="password">Password</Label>
            <div className="mt-2">
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                {...form.register("password")}
              />
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

          <div className="flex flex-col gap-3">
            <Button type="submit" variant="danger" className="w-full" loading={isDeleting}>
              Delete My Account
            </Button>
            <Link href="/dashboard" className="inline-flex w-full">
              <Button type="button" variant="secondary" className="w-full">
                Cancel and go back to dashboard
              </Button>
            </Link>
          </div>
        </form>
      </Card>

      <ConfirmDialog
        isOpen={isConfirmOpen}
        title="Are you sure?"
        message="This cannot be undone. This will permanently delete your account, sites, and analytics."
        confirmText="Yes, delete my account"
        cancelText="No, keep my account"
        variant="danger"
        loading={isDeleting}
        onCancel={() => setIsConfirmOpen(false)}
        onConfirm={deleteAccount}
      />
    </div>
  );
}

