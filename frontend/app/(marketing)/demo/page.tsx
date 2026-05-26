import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export default function DemoPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
      <Card className="relative overflow-hidden p-10">
        <div className="absolute inset-0 dot-grid opacity-60" aria-hidden="true" />
        <div className="relative">
          <h1 className="text-3xl font-semibold tracking-tight">Live demo coming soon</h1>
          <p className="mt-3 max-w-2xl text-base text-textSecondary">
            The demo dashboard will showcase Metrika’s own analytics once the demo site is created in the database.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link href="/register" className="inline-flex">
              <Button>Start Free Trial</Button>
            </Link>
            <Link href="/" className="inline-flex">
              <Button variant="secondary">Back to Home</Button>
            </Link>
          </div>
        </div>
      </Card>
    </div>
  );
}

