"use client";

import * as React from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Skeleton } from "@/components/ui/Skeleton";
import { useApi } from "@/lib/useApi";
import { applyApiFieldErrors } from "@/lib/formErrors";
import { ApiError } from "@/lib/errors";
import { toast } from "@/lib/toast";
import type { User } from "@/types/user";

const nameSchema = z.object({
  name: z.string().min(2, "Name is required"),
});
type NameValues = z.infer<typeof nameSchema>;

const passwordRules = z
  .string()
  .min(8, "At least 8 characters")
  .regex(/[A-Z]/, "Include an uppercase letter")
  .regex(/[0-9]/, "Include a number")
  .regex(/[^A-Za-z0-9]/, "Include a special character");

const passwordSchema = z
  .object({
    currentPassword: z.string().min(1, "Current password is required"),
    newPassword: passwordRules,
    confirmPassword: z.string().min(1, "Confirm your new password"),
  })
  .refine((v) => v.newPassword === v.confirmPassword, { message: "Passwords do not match", path: ["confirmPassword"] });

type PasswordValues = z.infer<typeof passwordSchema>;

export default function ProfilePage() {
  const api = useApi();
  const qc = useQueryClient();

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: () => api.get<User>("/api/auth/me/"),
  });

  const nameForm = useForm<NameValues>({
    resolver: zodResolver(nameSchema),
    values: meQuery.data ? { name: meQuery.data.name } : { name: "" },
  });

  const passwordForm = useForm<PasswordValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: { currentPassword: "", newPassword: "", confirmPassword: "" },
  });

  const [nameSaved, setNameSaved] = React.useState(false);
  const [passwordSaved, setPasswordSaved] = React.useState(false);
  const [nameError, setNameError] = React.useState<string | null>(null);
  const [passwordError, setPasswordError] = React.useState<string | null>(null);

  const saveName = nameForm.handleSubmit(async (values) => {
    setNameSaved(false);
    setNameError(null);
    try {
      await api.patch<User>("/api/auth/me/", { name: values.name });
      await qc.invalidateQueries({ queryKey: ["me"] });
      setNameSaved(true);
      toast.success("Name updated.");
    } catch (err) {
      const applied = applyApiFieldErrors(err, nameForm.setError);
      if (!applied) {
        const message = err instanceof ApiError ? err.message : "Unable to update name.";
        setNameError(message);
        toast.error(message);
      }
    }
  });

  const changePassword = passwordForm.handleSubmit(async (values) => {
    setPasswordSaved(false);
    setPasswordError(null);
    try {
      await api.post<Record<string, never>>("/api/auth/password-change/", {
        current_password: values.currentPassword,
        new_password: values.newPassword,
      });
      passwordForm.reset();
      setPasswordSaved(true);
      toast.success("Password changed successfully.");
    } catch (err) {
      const applied = applyApiFieldErrors(err, passwordForm.setError);
      if (!applied) {
        const message = err instanceof ApiError ? err.message : "Unable to change password.";
        setPasswordError(message);
        toast.error(message);
      }
    }
  });

  return (
    <div className="space-y-6">
      <div>
        <div className="text-2xl font-semibold tracking-tight">Profile</div>
        <div className="mt-1 text-sm text-textSecondary">Manage your account details and security.</div>
      </div>

      <Card className="p-6">
        <div className="text-base font-semibold">Account</div>
        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <div className="text-xs font-medium text-textSecondary">Email</div>
            <div className="mt-2">
              {meQuery.isLoading ? (
                <Skeleton className="h-10 w-full" />
              ) : (
                <Input value={meQuery.data?.email ?? ""} readOnly />
              )}
            </div>
          </div>
          <div>
            <div className="text-xs font-medium text-textSecondary">Member since</div>
            <div className="mt-2">
              {meQuery.isLoading ? (
                <Skeleton className="h-10 w-full" />
              ) : (
                <Input value={meQuery.data ? new Date(meQuery.data.date_joined).toLocaleDateString() : ""} readOnly />
              )}
            </div>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <div className="text-base font-semibold">Update name</div>
        <form onSubmit={saveName} className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <Label htmlFor="name">Name</Label>
            <div className="mt-2">
              <Input id="name" {...nameForm.register("name")} />
            </div>
            {nameForm.formState.errors.name ? (
              <p className="mt-2 text-sm text-danger">{nameForm.formState.errors.name.message}</p>
            ) : null}
          </div>

          {nameError ? (
            <div className="sm:col-span-2 rounded-md border border-danger/30 bg-danger/5 px-3 py-2 text-sm text-danger">
              {nameError}
            </div>
          ) : null}
          {nameSaved ? (
            <div className="sm:col-span-2 rounded-md border border-success/30 bg-success/5 px-3 py-2 text-sm text-success">
              Name updated.
            </div>
          ) : null}

          <div className="sm:col-span-2">
            <Button type="submit" loading={nameForm.formState.isSubmitting}>
              Save Changes
            </Button>
          </div>
        </form>
      </Card>

      <Card className="p-6">
        <div className="text-base font-semibold">Change password</div>
        <form onSubmit={changePassword} className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <Label htmlFor="currentPassword">Current password</Label>
            <div className="mt-2">
              <Input id="currentPassword" type="password" autoComplete="current-password" {...passwordForm.register("currentPassword")} />
            </div>
            {passwordForm.formState.errors.currentPassword ? (
              <p className="mt-2 text-sm text-danger">{passwordForm.formState.errors.currentPassword.message}</p>
            ) : null}
          </div>
          <div className="sm:col-span-1">
            <Label htmlFor="newPassword">New password</Label>
            <div className="mt-2">
              <Input id="newPassword" type="password" autoComplete="new-password" {...passwordForm.register("newPassword")} />
            </div>
            {passwordForm.formState.errors.newPassword ? (
              <p className="mt-2 text-sm text-danger">{passwordForm.formState.errors.newPassword.message}</p>
            ) : null}
          </div>
          <div className="sm:col-span-1">
            <Label htmlFor="confirmPassword">Confirm</Label>
            <div className="mt-2">
              <Input
                id="confirmPassword"
                type="password"
                autoComplete="new-password"
                {...passwordForm.register("confirmPassword")}
              />
            </div>
            {passwordForm.formState.errors.confirmPassword ? (
              <p className="mt-2 text-sm text-danger">{passwordForm.formState.errors.confirmPassword.message}</p>
            ) : null}
          </div>

          {passwordError ? (
            <div className="sm:col-span-2 rounded-md border border-danger/30 bg-danger/5 px-3 py-2 text-sm text-danger">
              {passwordError}
            </div>
          ) : null}
          {passwordSaved ? (
            <div className="sm:col-span-2 rounded-md border border-success/30 bg-success/5 px-3 py-2 text-sm text-success">
              Password changed successfully.
            </div>
          ) : null}

          <div className="sm:col-span-2">
            <Button type="submit" loading={passwordForm.formState.isSubmitting}>
              Change Password
            </Button>
          </div>
        </form>
      </Card>

      <Card className="border-danger/30 p-6">
        <div className="text-base font-semibold text-danger">Danger zone</div>
        <p className="mt-2 text-sm text-textSecondary">
          Permanently delete your account, sites, and analytics data.
        </p>
        <Link href="/delete-account" className="mt-5 inline-flex">
          <Button variant="danger" type="button">
            Delete Account
          </Button>
        </Link>
      </Card>
    </div>
  );
}
