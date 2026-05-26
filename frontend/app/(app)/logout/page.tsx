"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ConfirmDialog } from "@/components/dialog/ConfirmDialog";

export default function LogoutPage() {
  const { logout } = useAuth();
  const router = useRouter();
  const [isOpen, setIsOpen] = React.useState(true);
  const [isLoggingOut, setIsLoggingOut] = React.useState(false);

  const confirmLogout = async () => {
    setIsLoggingOut(true);
    await logout().catch(() => null);
    setIsLoggingOut(false);
  };

  return (
    <div className="mx-auto max-w-md py-10">
      <Card className="p-6">
        <h1 className="font-heading text-2xl font-semibold text-primary">Sign out</h1>
        <p className="mt-2 text-sm text-textSecondary">You can sign back in any time.</p>
        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <Button type="button" onClick={() => setIsOpen(true)}>
            Sign out
          </Button>
          <Button type="button" variant="secondary" onClick={() => router.push("/dashboard")}>
            Cancel
          </Button>
        </div>
      </Card>

      <ConfirmDialog
        isOpen={isOpen}
        title="Are you sure?"
        message="This will sign you out of Metrika on this browser."
        confirmText="Confirm"
        variant="primary"
        loading={isLoggingOut}
        onCancel={() => {
          setIsOpen(false);
          router.push("/dashboard");
        }}
        onConfirm={confirmLogout}
      />
    </div>
  );
}
