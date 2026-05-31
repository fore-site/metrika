"use client";

import * as React from "react";
import { ChevronDown } from "lucide-react";

type DropdownMenuProps = {
  /** The label / value shown on the button when the menu is closed. */
  label: string;
  children: React.ReactNode;
  className?: string;
};

export function DropdownMenu({ label, children, className }: DropdownMenuProps) {
  const [open, setOpen] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);

  // Close on outside click
  React.useEffect(() => {
    if (!open) return;
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        className="input flex h-11 w-full items-center justify-between text-left"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="truncate">{label}</span>
        <ChevronDown className="ml-2 h-4 w-4 flex-shrink-0 text-textSecondary" />
      </button>
      {open && (
        <div className={`absolute left-0 right-0 z-40 mt-1 rounded-xl border border-gray-200 bg-white shadow-sm ${className ?? ""}`}>
          <div className="py-1" onClick={() => setOpen(false)}>
            {children}
          </div>
        </div>
      )}
    </div>
  );
}