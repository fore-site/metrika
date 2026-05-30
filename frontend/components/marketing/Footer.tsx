import Link from "next/link";
import { Logo } from "@/components/branding/Logo";

export function MarketingFooter() {
  return (
    <footer className="mt-20 bg-gray-900 text-gray-300">
      <div className="mx-auto grid max-w-6xl grid-cols-1 gap-10 px-4 py-14 sm:px-6 md:grid-cols-3">
        <div>
          <Logo className="text-white" href="/" />
          <p className="mt-4 text-sm text-gray-400">
            Web analytics built for teams that want clarity without compromise.
          </p>
        </div>
        <div>
          <div className="text-sm font-semibold text-white">Product</div>
          <ul className="mt-4 space-y-2 text-sm">
            <li>
              <a className="hover:text-white" href="/#features">
                Features
              </a>
            </li>
            <li>
              <a className="hover:text-white" href="/pricing">
                Pricing
              </a>
            </li>
            <li>
              <a className="hover:text-white" href="/dashboard">
                Dashboard
              </a>
            </li>
          </ul>
        </div>
        <div>
          <div className="text-sm font-semibold text-white">Company</div>
          <ul className="mt-4 space-y-2 text-sm">
            <li>
              <a className="hover:text-white" href="/docs">
                Docs
              </a>
            </li>
            <li>
              <a className="hover:text-white" href="/register">
                Start Free Trial
              </a>
            </li>
            <li>
              <a className="hover:text-white" href="mailto:noreply.metrika@gmail.com">
                Support
              </a>
            </li>
          </ul>
        </div>
      </div>
      <div className="border-t border-gray-800">
        <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-4 px-4 py-6 text-xs text-gray-500 sm:flex-row sm:items-center sm:px-6">
          <div>© {new Date().getFullYear()} Metrika. All rights reserved.</div>
          <div className="flex gap-4">
            <a className="hover:text-gray-300" href="#">
              Privacy
            </a>
            <a className="hover:text-gray-300" href="#">
              Terms
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
