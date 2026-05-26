import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#6366F1",
          hover: "#4F46E5"
        },
        success: "#10B981",
        danger: "#EF4444",
        warning: "#F59E0B",
        background: "#F9FAFB",
        surface: "#FFFFFF",
        textPrimary: "#111827",
        textSecondary: "#6B7280",
        border: "#E5E7EB",
        chart: {
          1: "#6366F1",
          2: "#10B981",
          3: "#F59E0B",
          4: "#EF4444",
          5: "#8B5CF6",
          6: "#EC4899"
        }
      },
      fontFamily: {
        heading: ["var(--font-space-grotesk)", "system-ui", "sans-serif"],
        body: ["var(--font-inter)", "system-ui", "sans-serif"]
      },
      borderRadius: {
        xl: "12px"
      },
      boxShadow: {
        card: "0 1px 2px rgba(0,0,0,0.05)"
      }
    }
  },
  plugins: []
} satisfies Config;

