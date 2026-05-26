"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { applyApiFieldErrors } from "@/lib/formErrors";
import { ApiError } from "@/lib/errors";
import { useApi } from "@/lib/useApi";
import { toast } from "@/lib/toast";
import type { Site } from "@/types/site";

const schema = z.object({
  domain: z.string().min(3, "Enter a domain (e.g. example.com)"),
  timezone: z.string().min(1, "Timezone is required"),
});

type FormValues = z.infer<typeof schema>;

const timezones = ["UTC", "Africa/Lagos", "America/New_York", "Europe/London", "Europe/Paris", "Asia/Tokyo"];

export function CreateSiteCard() {
  const api = useApi();
  const qc = useQueryClient();
  const [serverError, setServerError] = React.useState<string | null>(null);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { domain: "", timezone: "UTC" },
  });

  const onSubmit = form.handleSubmit(async (values) => {
    setServerError(null);
    try {
      await api.post<Site>("/api/sites/", values);
      await qc.invalidateQueries({ queryKey: ["sites"] });
      form.reset({ domain: "", timezone: values.timezone });
      toast.success("Site created successfully.");
    } catch (err) {
      const applied = applyApiFieldErrors(err, form.setError);
      if (!applied) {
        const message = err instanceof ApiError ? err.message : "Unable to create site.";
        setServerError(message);
        toast.error(message);
      }
    }
  });

  return (
    <Card className="relative overflow-hidden p-8">
      <div className="absolute inset-0 dot-grid opacity-50" aria-hidden="true" />
      <div className="relative">
        <div className="text-xl font-semibold">Create your first site</div>
        <div className="mt-2 text-sm text-textSecondary">
          Add your domain and we’ll generate a tracking snippet you can paste into your site.
        </div>

        <form onSubmit={onSubmit} className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <Label htmlFor="domain">Domain</Label>
            <div className="mt-2">
              <Input id="domain" placeholder="example.com" {...form.register("domain")} />
            </div>
            {form.formState.errors.domain ? (
              <p className="mt-2 text-sm text-danger">{form.formState.errors.domain.message}</p>
            ) : null}
          </div>

          <div className="sm:col-span-2">
            <Label htmlFor="timezone">Timezone</Label>
            <div className="mt-2">
              <select id="timezone" className="input" {...form.register("timezone")}>
                {timezones.map((tz) => (
                  <option key={tz} value={tz}>
                    {tz}
                  </option>
                ))}
              </select>
            </div>
            {form.formState.errors.timezone ? (
              <p className="mt-2 text-sm text-danger">{form.formState.errors.timezone.message}</p>
            ) : null}
          </div>

          {serverError ? (
            <div className="sm:col-span-2 rounded-md border border-danger/30 bg-danger/5 px-3 py-2 text-sm text-danger">
              {serverError}
            </div>
          ) : null}

          <div className="sm:col-span-2">
            <Button type="submit" className="w-full" loading={form.formState.isSubmitting}>
              Create Site
            </Button>
          </div>
        </form>
      </div>
    </Card>
  );
}
