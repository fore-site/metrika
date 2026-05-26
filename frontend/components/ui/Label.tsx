import * as React from "react";
import { clsx } from "clsx";

export function Label(props: React.LabelHTMLAttributes<HTMLLabelElement>) {
  const { className, ...rest } = props;
  return <label className={clsx("text-sm font-medium text-textPrimary", className)} {...rest} />;
}

