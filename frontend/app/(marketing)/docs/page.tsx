"use client";

import * as React from "react";
import Link from "next/link";
import { Check, Copy, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { toast } from "@/lib/toast";

const frontendUrl =
  process.env.NEXT_PUBLIC_FRONTEND_URL ||
  (typeof window !== "undefined" ? window.location.origin : "https://metrika-five.vercel.app");

const snippet = `<script async defer
  data-domain="example.com"
  data-token="abc123..."
  src="${frontendUrl}/js/tracker.js">
</script>`;

const metrics = [
  ["Unique Visitors", "The number of distinct people who visited your site in the selected period."],
  ["Pageviews", "The total number of pages viewed, including repeat views."],
  ["Total Visits", "The total number of browsing sessions recorded for your site."],
  ["Bounce Rate", "The percentage of visits where someone viewed only one page."],
  ["Views Per Visit", "The average number of pages viewed during each visit."],
  ["Avg Duration", "The average time visitors spend during a visit."],
];

const faqs = [
  ["Is it free?", "Yes. Metrika is free during beta and no credit card is required."],
  ["Can I self-host?", "Yes. Metrika is designed so teams can run it on their own infrastructure when they need full control."],
  ["What about privacy?", "Metrika focuses on useful aggregate analytics without invasive tracking patterns."],
];

export default function DocsPage() {
  const [copied, setCopied] = React.useState(false);
  const [showInstructions, setShowInstructions] = React.useState(false);

  const copySnippet = async () => {
    await navigator.clipboard.writeText(snippet);
    setCopied(true);
    toast.success("Snippet copied.");
    setTimeout(() => setCopied(false), 1400);
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-16 sm:px-6">
      <div className="mb-10">
        <h1 className="font-heading text-[30px] font-semibold text-primary">Documentation</h1>
        <p className="mt-3 text-base text-textSecondary">Get started with Metrika in minutes.</p>
      </div>

      <div className="space-y-8">
        <section>
          <h2 className="font-heading text-xl font-semibold text-textPrimary">1. Create an account</h2>
          <p className="mt-2 text-sm leading-6 text-textSecondary">
            Sign up for a free Metrika account, verify your email, and you will be ready to add your first site.
            <a href="/register" className="ml-1 font-medium text-primary hover:underline">
              Create an account
            </a>
            .
          </p>
        </section>

        <section>
          <h2 className="font-heading text-xl font-semibold text-textPrimary">2. Add your site</h2>
          <p className="mt-2 text-sm leading-6 text-textSecondary">
            Enter your domain name and receive a unique tracking token.
          </p>
        </section>

        <section>
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="font-heading text-xl font-semibold text-textPrimary">3. Install the snippet</h2>
              <p className="mt-2 text-sm leading-6 text-textSecondary">
                Place the snippet before closing <code className="rounded bg-gray-100 px-1.5 py-0.5">{"</head>"}</code> on your base HTML or in an equivalent metadata 
                in your jsx/tsx file.
              </p>
            </div>
            <Button variant="secondary" type="button" onClick={copySnippet}>
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              {copied ? "Copied" : "Copy"}
            </Button>
          </div>
          <pre className="mt-4 overflow-x-auto rounded-xl border border-gray-200 bg-gray-50 p-4 text-sm text-textPrimary">
            <code>{snippet}</code>
          </pre>

          {/* Installation instructions */}
          <button
            className="mt-2 flex items-center gap-1 text-xs text-primary hover:underline focus:outline-none"
            onClick={() => setShowInstructions(!showInstructions)}
          >
            {showInstructions ? (
              <>
                <ChevronUp className="h-3 w-3" /> Hide instructions
              </>
            ) : (
              <>
                <ChevronDown className="h-3 w-3" /> How to install
              </>
            )}
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
  data-domain="example.com"
  data-token="abc123..."
  src="${frontendUrl}/js/tracker.js"
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
        </section>

        <section>
          <h2 className="font-heading text-xl font-semibold text-textPrimary">4. View your dashboard</h2>
          <p className="mt-2 text-sm leading-6 text-textSecondary">
            That's it! Your analytics will appear in real time.
          </p>
        </section>

        <section>
          <h2 className="font-heading text-xl font-semibold text-textPrimary">Metrics explained</h2>
          <Card className="mt-4 p-0">
            <dl className="divide-y divide-gray-200">
              {metrics.map(([name, definition]) => (
                <div key={name} className="grid gap-1 px-6 py-4 sm:grid-cols-[180px_1fr] sm:gap-6">
                  <dt className="text-sm font-medium text-textPrimary">{name}</dt>
                  <dd className="text-sm leading-6 text-textSecondary">{definition}</dd>
                </div>
              ))}
            </dl>
          </Card>
        </section>

        <section>
          <h2 className="font-heading text-xl font-semibold text-textPrimary">FAQ</h2>
          <div className="mt-4 space-y-4">
            {faqs.map(([question, answer]) => (
              <Card key={question} className="p-5">
                <h3 className="text-sm font-semibold text-textPrimary">{question}</h3>
                <p className="mt-2 text-sm leading-6 text-textSecondary">{answer}</p>
              </Card>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}