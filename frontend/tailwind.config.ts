import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Background hierarchy
        "bg-base": "#0d1117",
        "bg-surface": "#161b22",
        "bg-elevated": "#21262d",
        "bg-subtle": "#30363d",
        // Text
        "text-primary": "#e6edf3",
        "text-secondary": "#8b949e",
        "text-muted": "#484f58",
        "text-link": "#58a6ff",
        // Severity
        "severity-critical": "#ff6e6e",
        "severity-high": "#ff9500",
        "severity-medium": "#e3b341",
        "severity-low": "#3fb950",
        "severity-info": "#58a6ff",
        // Status
        "status-success": "#3fb950",
        "status-warning": "#e3b341",
        "status-error": "#ff6e6e",
        "status-running": "#58a6ff",
        // Brand
        "accent-primary": "#7c5cfc",
        "accent-hover": "#9474ff",
        // Border
        "border-default": "#30363d",
        "border-muted": "#21262d",
        "border-emphasis": "#484f58",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "Consolas", "monospace"],
      },
      fontSize: {
        xs: ["11px", "1.5"],
        sm: ["12px", "1.5"],
        base: ["14px", "1.5"],
        md: ["16px", "1.5"],
        lg: ["20px", "1.5"],
        xl: ["24px", "1.5"],
        "2xl": ["32px", "1.5"],
      },
      borderRadius: {
        sm: "4px",
        md: "6px",
        lg: "8px",
      },
      spacing: {
        1: "4px",
        2: "8px",
        3: "12px",
        4: "16px",
        5: "20px",
        6: "24px",
        8: "32px",
        12: "48px",
        16: "64px",
      },
    },
  },
  plugins: [],
};

export default config;
