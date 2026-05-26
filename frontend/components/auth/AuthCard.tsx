import * as React from "react";
import { Card } from "@/components/ui/Card";
import { Logo } from "@/components/branding/Logo";

export function AuthCard(props: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div className="w-full max-w-md">
      <div className="mb-6 flex justify-center">
        <Logo />
      </div>
      <Card className="p-6 sm:p-8">
        <h1 className="text-2xl font-semibold tracking-tight">{props.title}</h1>
        {props.subtitle ? <p className="mt-2 text-sm text-textSecondary">{props.subtitle}</p> : null}
        <div className="mt-6">{props.children}</div>
      </Card>
    </div>
  );
}

