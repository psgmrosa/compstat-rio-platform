import type { Config } from "tailwindcss";

/**
 * Design tokens da CompStat Rio.
 * Paleta institucional (azul Rio) + status de risco (alto/médio/baixo).
 * Não inventar cores ad-hoc no JSX — usar essas tokens.
 */
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        rio: {
          ink: "#0F1B2D",
          900: "#0F2240",
          800: "#1F3A5F",
          700: "#2E4D78",
          600: "#3D5A80",
          100: "#E8EEF6",
          50: "#F4F7FC",
        },
        risk: {
          high: "#B22222",
          med: "#E67E22",
          low: "#27AE60",
        },
        surface: "#FFFFFF",
        bg: "#F7F8FA",
        muted: "#5A6B7E",
        border: "#E5E9EF",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        display: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "monospace"],
      },
      borderRadius: {
        xl: "12px",
        "2xl": "16px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(15, 27, 45, 0.04), 0 4px 12px rgba(15, 27, 45, 0.06)",
        hover:
          "0 2px 4px rgba(15, 27, 45, 0.06), 0 12px 28px rgba(15, 27, 45, 0.10)",
      },
      fontSize: {
        kpi: ["32px", { lineHeight: "1", letterSpacing: "-0.02em" }],
        hero: ["44px", { lineHeight: "1", letterSpacing: "-0.025em" }],
      },
    },
  },
  plugins: [],
};

export default config;
