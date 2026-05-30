import { Logo } from "@/components/branding/Logo";
import { DateRangePicker } from "@/components/dashboard/DateRangePicker";

export function DemoTopNav() {
  return (
    <header className="sticky top-0 z-30 border-b border-gray-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
        <Logo href="/demo" />
        <div className="flex items-center gap-3">
          <DateRangePicker />
        </div>
      </div>
    </header>
  );
}