import * as React from "react";
import { clsx } from "clsx";

export function Card(props: React.HTMLAttributes<HTMLDivElement>) {
  const { className, ...rest } = props;
  return <div className={clsx("card", className)} {...rest} />;
}

