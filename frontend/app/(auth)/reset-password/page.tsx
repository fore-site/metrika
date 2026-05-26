"use client";

import { useSearchParams, useRouter } from "next/navigation";
import * as React from "react";

export default function ResetPasswordAliasPage() {
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

