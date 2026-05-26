import Link from "next/link";
import { clsx } from "clsx";

export function Logo({ className, href = "/" }: { className?: string; href?: string }) {
  return (
    <Link href={href} className={clsx("inline-flex items-center gap-2", className)} aria-label="Metrika">
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary text-white shadow-sm">
        <span className="font-heading text-sm font-semibold">M</span>
      </span>
      <span className="font-heading text-lg font-semibold tracking-tight text-textPrimary">Metrika</span>
    </Link>
  );
}

