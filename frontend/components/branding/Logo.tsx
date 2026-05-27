import Link from "next/link";
import { clsx } from "clsx";

export function Logo({ className, href = "/" }: { className?: string; href?: string }) {
  return (
    <Link href={href} className={clsx("inline-flex items-center gap-2", className)} aria-label="Metrika">
      {/* Icon container — same size, background & shadow as before */}
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary text-white shadow-sm">
        {/* Stylized M made of bar chart bars */}
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M4 18 L4 6 L10 14 L14 8 L20 4 L20 18"
            stroke="white"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />

          <circle cx="4" cy="6" r="2" fill="white" />
          <circle cx="14" cy="8" r="2" fill="white" />
          <circle cx="20" cy="4" r="2" fill="white" />
        </svg>
      </span>

      {/* Wordmark — unchanged */}
      <span className="font-heading text-lg font-semibold tracking-tight text-textPrimary">
        Metrika
      </span>
    </Link>
  );
}