import Link from "next/link";
import { CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

const features = [
  "Up to 10,000 monthly pageviews",
  "Unlimited sites",
  "All analytics features",
  "Email reports (coming soon)",
  "Community support",
];

export default function PricingPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-20 sm:px-6">
      <section className="text-center">
        <h1 className="font-heading text-4xl font-semibold text-textPrimary sm:text-5xl">Simple, transparent pricing</h1>
        <p className="mt-4 text-lg text-textSecondary">Free during beta. No credit card required.</p>
      </section>

      <section className="mt-12 flex justify-center">
        <Card className="w-full max-w-md p-8">
          <div className="text-sm font-medium text-primary">Free Forever</div>
          <div className="mt-3 flex items-end gap-1">
            <span className="font-heading text-4xl font-semibold text-textPrimary">$0</span>
            <span className="pb-1 text-sm text-textSecondary">/month</span>
          </div>
          <ul className="mt-8 space-y-4">
            {features.map((feature) => (
              <li key={feature} className="flex items-start gap-3 text-sm text-textSecondary">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                <span>{feature}</span>
              </li>
            ))}
          </ul>
          <Link href="/register" className="mt-8 inline-flex w-full">
            <Button className="w-full">Start Free Trial</Button>
          </Link>
        </Card>
      </section>

      <p className="mx-auto mt-8 max-w-xl text-center text-sm leading-6 text-textSecondary">
        Need more pageviews? Self-host Metrika on your own server for unlimited scale.{" "}
        <a
          href="https://github.com/"
          target="_blank"
          rel="noreferrer"
          className="font-medium text-primary hover:underline"
        >
          Check out our GitHub
        </a>
        .
      </p>
    </div>
  );
}

