"use client";

import { Toaster } from "react-hot-toast";

export function AppToaster() {
  return (
    <Toaster
      position="top-right"
      toastOptions={{
        duration: 5000,
      }}
      gutter={10}
      containerStyle={{ top: 16, right: 16 }}
    />
  );
}

