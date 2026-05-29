"use client";

import { useSearchParams, useRouter } from "next/navigation";
import * as React from "react";

function ResetPasswordAlias() {
  const sp = useSearchParams();
  const router = useRouter();

  React.useEffect(() => {
    const uid = sp.get("uid");
    const token = sp.get("token");
    const params = new URLSearchParams();
    if (uid) params.set("uid", uid);
    if (token) params.set("token", token);
    router.replace(`/password-reset/confirm?${params.toString()}`);
  }, [router, sp]);

  return null;
}

export default function ResetPasswordAliasPage() {
  return (
    <React.Suspense fallback={<div className="min-h-screen bg-background" />}>
      <ResetPasswordAlias />
    </React.Suspense>
  );
}

