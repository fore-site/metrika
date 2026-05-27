import { MarketingFooter } from "@/components/marketing/Footer";
import { Logo } from "@/components/branding/Logo";
import Link from "next/link";
import { Button } from "@/components/ui/Button";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <header className="top-0 z-30 border-b border-gray-200/70 backdrop-blur">
            <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
              <Logo />
              <div className="flex items-center gap-3">
                <Link href="/login">
                  <Button variant="secondary">Sign In</Button>
                </Link>
              </div>
            </div>
      </header>
      <div className="relative flex min-h-screen items-center justify-center px-4 py-12">
        <div className="absolute inset-0 dot-grid opacity-60" aria-hidden="true" />
        <div className="relative w-full max-w-md">{children}</div>
      </div>
      <MarketingFooter />
    </div>
  );
}

