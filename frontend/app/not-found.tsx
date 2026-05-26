import Link from "next/link";
import { Button } from "@/components/ui/Button";

export default function NotFound() {
  return (
    <main className="dot-grid grid min-h-screen place-items-center bg-background px-4 py-12">
      <div className="w-full max-w-md rounded-xl border border-gray-200 bg-white p-8 text-center shadow-sm">
        <div className="font-heading text-[30px] font-semibold text-primary">404</div>
        <h1 className="mt-3 font-heading text-2xl font-semibold text-textPrimary">Page not found</h1>
        <p className="mt-3 text-sm leading-6 text-textSecondary">
          The page you are looking for does not exist or may have moved.
        </p>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
          <Link href="/dashboard" className="inline-flex">
            <Button>Go to Dashboard</Button>
          </Link>
          <Link href="/" className="inline-flex">
            <Button variant="secondary">Go Home</Button>
          </Link>
        </div>
      </div>
    </main>
  );
}

