import { AuthCard } from "@/components/auth/AuthCard";
import { Button } from "@/components/ui/Button";

export default function VerifiedPage() {
  return (
    <AuthCard title="Email verified!" subtitle="You can now sign in to your account.">
      <a href="/login" className="inline-flex w-full">
        <Button className="w-full">Go to Login</Button>
      </a>
    </AuthCard>
  );
}

