"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Skeleton } from "@/components/ui/Skeleton";
import { ConfirmDialog } from "@/components/dialog/ConfirmDialog";
import { useApi } from "@/lib/useApi";
import { applyApiFieldErrors } from "@/lib/formErrors";
import { ApiError } from "@/lib/errors";
import { toast } from "@/lib/toast";
import type { Site } from "@/types/site";

const schema = z.object({
  domain: z.string().min(3, "Enter a valid domain"),
  timezone: z.string().min(1, "Timezone is required"),
});

type FormValues = z.infer<typeof schema>;

const timezones = [
  "UTC",
  "Africa/Lagos",
  "America/New_York",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Paris",
  "Asia/Dubai",
  "Asia/Tokyo",
];

function TrackingSnippet(props: { site: Site }) {
  const frontendUrl = process.env.NEXT_PUBLIC_FRONTEND_URL || window.location.origin;
  const src = `${frontendUrl}/js/tracker.js`;
  const [copied, setCopied] = React.useState(false);
  const [showInstructions, setShowInstructions] = React.useState(false);

  const code = `<script async defer
    data-domain="${props.site.domain}"
    data-token="${props.site.tracking_token}"
    src="${src}">
  </script>`;

  return (
    <div className="mt-4">
      <div className="flex items-center justify-between">
        <div className="text-sm font-medium text-textPrimary">Tracking snippet</div>
        <Button
          variant="secondary"
          type="button"
          onClick={async () => {
            await navigator.clipboard.writeText(code);
            setCopied(true);
            toast.success("Snippet copied.");
            setTimeout(() => setCopied(false), 1200);
          }}
        >
          {copied ? "Copied" : "Copy"}
        </Button>
      </div>

      <pre className="mt-3 overflow-auto rounded-xl border border-gray-200 bg-gray-50 p-4 text-xs text-textPrimary">
        <code>{code}</code>
      </pre>

      {/* Installation instructions */}
      <button
        className="mt-2 text-xs text-primary hover:underline focus:outline-none"
        onClick={() => setShowInstructions(!showInstructions)}
      >
        {showInstructions ? "Hide instructions" : "How to install"}
      </button>

      {showInstructions && (
        <div className="mt-3 space-y-4 text-sm text-textSecondary">
          <div>
            <div className="font-medium text-textPrimary">Plain HTML/Frameworks with index.html entry</div>
            <p className="mt-1">
              Paste the snippet just before the closing <code className="rounded bg-gray-50 px-1 text-xs">&lt;/head&gt;</code> tag in your 
              site's main <code className="rounded bg-gray-50 px-1 text-xs">index.html</code> or equivalent main HTML entry file.
            </p>
          </div>
          <div>
            <div className="font-medium text-textPrimary">WordPress</div>
            <p className="mt-1">
              Install a plugin like “Insert Headers and Footers” or “WPCode”, then add the snippet in the header section.
            </p>
          </div>
          <div>
            <div className="font-medium text-textPrimary">Next.js</div>
            <p className="mt-1">
              In your <code className="rounded bg-gray-50 px-1 text-xs">app/layout.tsx</code>, use the Next.js Script component:
            </p>
            <pre className="mt-2 overflow-auto rounded-lg border border-gray-200 bg-gray-50 p-3 text-xs text-textPrimary">
  {`<Script
    strategy="beforeInteractive"
    data-domain="${props.site.domain}"
    data-token="${props.site.tracking_token}"
    src="${src}"
  />`}
            </pre>
          </div>
          <div>
            <div className="font-medium text-textPrimary">Other platforms (Shopify, Squarespace, etc.)</div>
            <p className="mt-1">
              Look for a “Custom Code” or “Header HTML” section in your site’s admin panel and paste the snippet there.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function SiteSettingsPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const api = useApi();
  const qc = useQueryClient();
  const router = useRouter();

  const siteQuery = useQuery({
    queryKey: ["site", id],
    queryFn: () => api.get<Site>(`/api/sites/${id}/`),
  });

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    values: siteQuery.data ? { domain: siteQuery.data.domain, timezone: siteQuery.data.timezone } : { domain: "", timezone: "UTC" },
  });

  const [saved, setSaved] = React.useState(false);
  const [serverError, setServerError] = React.useState<string | null>(null);
  const [dangerOpen, setDangerOpen] = React.useState(false);
  const [isDeactivating, setIsDeactivating] = React.useState(false);

  const onSave = form.handleSubmit(async (values) => {
    setSaved(false);
    setServerError(null);
    try {
      await api.put<Site>(`/api/sites/${id}/`, values);
      await qc.invalidateQueries({ queryKey: ["sites"] });
      await qc.invalidateQueries({ queryKey: ["site", id] });
      setSaved(true);
      toast.success("Settings saved.");
    } catch (err) {
      const applied = applyApiFieldErrors(err, form.setError);
      if (!applied) {
        const message = err instanceof ApiError ? err.message : "Unable to save changes.";
        setServerError(message);
        toast.error(message);
      }
    }
  });

  const deactivate = async () => {
    setServerError(null);
    setIsDeactivating(true);
    try {
      await api.del<Record<string, never>>(`/api/sites/${id}/`);
      await qc.invalidateQueries({ queryKey: ["sites"] });
      toast.success("Site deactivated.");
      router.push("/dashboard");
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Unable to deactivate site.";
      setServerError(message);
      toast.error(message);
    } finally {
      setIsDeactivating(false);
      setDangerOpen(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="text-2xl font-semibold tracking-tight">Site settings</div>
        <div className="mt-1 text-sm text-textSecondary">Manage your domain, timezone, and snippet.</div>
      </div>

      <Card className="p-6">
        {siteQuery.isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-40 w-full" />
          </div>
        ) : siteQuery.error ? (
          <div className="rounded-md border border-danger/30 bg-danger/5 px-3 py-3 text-sm text-danger">
            {siteQuery.error instanceof ApiError ? siteQuery.error.message : "Unable to load site."}
          </div>
        ) : siteQuery.data ? (
          <>
            <form onSubmit={onSave} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <Label htmlFor="domain">Domain</Label>
                <div className="mt-2">
                  <Input id="domain" {...form.register("domain")} />
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
              {saved ? (
                <div className="sm:col-span-2 rounded-md border border-success/30 bg-success/5 px-3 py-2 text-sm text-success">
                  Changes saved.
                </div>
              ) : null}

              <div className="sm:col-span-2 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <Button type="submit" loading={form.formState.isSubmitting}>
                  Save Changes
                </Button>
                <Button variant="danger" type="button" onClick={() => setDangerOpen(true)}>
                  Deactivate Site
                </Button>
              </div>
            </form>

            <TrackingSnippet site={siteQuery.data} />
          </>
        ) : null}
      </Card>

      <ConfirmDialog
        isOpen={dangerOpen}
        title="Are you sure?"
        message="This will deactivate the site and stop data collection. You can re-add it later by creating a new site."
        confirmText="Deactivate Site"
        variant="danger"
        loading={isDeactivating}
        onCancel={() => setDangerOpen(false)}
        onConfirm={deactivate}
      />
    </div>
  );
}
