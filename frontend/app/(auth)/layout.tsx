export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <div className="relative flex min-h-screen items-center justify-center px-4 py-12">
        <div className="absolute inset-0 dot-grid opacity-60" aria-hidden="true" />
        <div className="relative w-full max-w-md">{children}</div>
      </div>
    </div>
  );
}

