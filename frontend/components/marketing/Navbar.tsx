import Link from "next/link";
import { Logo } from "@/components/branding/Logo";
import { Button } from "@/components/ui/Button";

export function MarketingNavbar() {
  return (
    <header className="sticky top-0 z-30 border-b border-gray-200/70 bg-white/70 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <Logo />
        <nav className="hidden items-center gap-6 text-sm text-textSecondary md:flex">
          <Link className="hover:text-textPrimary" href="/pricing">
            Pricing
          </Link>
          <Link className="hover:text-textPrimary" href="/docs">
            Docs
          </Link>
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/login">
            <Button variant="secondary">Sign In</Button>
          </Link>
        </div>
      </div>
    </header>
  );
}

