import { ArrowRight, Shield, Gauge, Zap } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

function SectionHeading(props: { eyebrow?: string; title: string; subtitle: string }) {
  return (
    <div className="mx-auto max-w-2xl text-center">
      {props.eyebrow ? <div className="text-sm font-medium text-primary">{props.eyebrow}</div> : null}
      <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">{props.title}</h2>
      <p className="mt-3 text-base text-textSecondary">{props.subtitle}</p>
    </div>
  );
}

export default function HomePage() {
  return (
    <div>
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 dot-grid opacity-70" aria-hidden="true" />
        <div className="relative mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-24">
          <div className="max-w-2xl mx-auto text-center">
            <h1 className="font-heading text-4xl font-semibold tracking-tight sm:text-6xl">
              The Complete{" "}
              <span className="text-primary">Analytics Toolkit</span>
            </h1>
            <p className="mt-5 text-lg text-textSecondary">
              Metrika gives you cloud-hosted analytics without invasive tracking. Own your data, respect your users, and
              ship decisions faster.
            </p>
            <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
              <a href="/register" className="inline-flex">
                <Button>
                  Get Started For Free <ArrowRight className="h-4 w-4" />
                </Button>
              </a>
              <a href="/demo" className="inline-flex">
                <Button variant="secondary">View Live Demo</Button>
              </a>
            </div>
            <div className="mt-10 grid grid-cols-1 gap-3 sm:grid-cols-3">
              <Card className="p-4">
                <div className="text-sm font-semibold">No cookies by default</div>
                <div className="mt-1 text-sm text-textSecondary">Privacy-first collection for modern sites.</div>
              </Card>
              <Card className="p-4">
                <div className="text-sm font-semibold">Fast setup</div>
                <div className="mt-1 text-sm text-textSecondary">Copy a snippet, start seeing traffic.</div>
              </Card>
              <Card className="p-4">
                <div className="text-sm font-semibold">Actionable insights</div>
                <div className="mt-1 text-sm text-textSecondary">Clean dashboards built for teams.</div>
              </Card>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <SectionHeading
          eyebrow="How it works"
          title="Up and running in minutes"
          subtitle="Create a project, add your site, and paste a single script tag."
        />
        <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-3">
          <Card>
            <div className="text-sm font-semibold text-textPrimary">1) Sign Up</div>
            <div className="mt-2 text-sm text-textSecondary">Create your account and verify your email.</div>
          </Card>
          <Card>
            <div className="text-sm font-semibold text-textPrimary">2) Add Your Site</div>
            <div className="mt-2 text-sm text-textSecondary">Create a site, pick a timezone, and get a token.</div>
          </Card>
          <Card>
            <div className="text-sm font-semibold text-textPrimary">3) Copy &amp; Paste</div>
            <div className="mt-2 text-sm text-textSecondary">Embed the script and watch analytics populate.</div>
          </Card>
        </div>
      </section>

      <section id="features" className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <SectionHeading
          eyebrow="Everything you need"
          title="Analytics without compromise"
          subtitle="A dashboard you’ll love, backed by privacy-respecting collection."
        />
        <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-3">
          <Card>
            <div className="flex items-center gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-lg bg-primary/10 text-primary">
                <Shield className="h-5 w-5" />
              </span>
              <div className="text-base font-semibold">Privacy by Design</div>
            </div>
            <p className="mt-3 text-sm text-textSecondary">Minimize data collection while keeping metrics useful.</p>
          </Card>
          <Card>
            <div className="flex items-center gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-lg bg-success/10 text-success">
                <Gauge className="h-5 w-5" />
              </span>
              <div className="text-base font-semibold">User-Friendly Dashboard</div>
            </div>
            <p className="mt-3 text-sm text-textSecondary">Trend lines, top pages, referrers, geography, and tech.</p>
          </Card>
          <Card>
            <div className="flex items-center gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-lg bg-warning/10 text-warning">
                <Zap className="h-5 w-5" />
              </span>
              <div className="text-base font-semibold">Lightweight &amp; Fast</div>
            </div>
            <p className="mt-3 text-sm text-textSecondary">A tiny snippet that stays out of your performance budget.</p>
          </Card>
        </div>
      </section>

      <section id="docs" className="mx-auto max-w-6xl px-4 pb-4 pt-10 sm:px-6">
        <div className="card relative overflow-hidden">
          <div className="absolute inset-0 dot-grid opacity-60" aria-hidden="true" />
          <div className="relative flex flex-col items-start justify-between gap-6 md:flex-row md:items-center">
            <div>
              <div className="text-sm font-medium text-primary">Ready to understand your traffic?</div>
              <div className="mt-2 text-2xl font-semibold">Create your free account and ship smarter.</div>
              <div className="mt-2 text-sm text-textSecondary">Get set up in minutes.</div>
            </div>
            <a href="/register" className="inline-flex">
              <Button>
                Create Free Account <ArrowRight className="h-4 w-4" />
              </Button>
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}

