import { clsx } from "clsx";

type Severity = "critical" | "high" | "medium" | "low" | "info";
type Variant = "filled" | "outline" | "dot";

interface Props {
  severity: string;
  variant?: Variant;
  className?: string;
}

const SEVERITY_CONFIG: Record<Severity, { label: string; color: string; bg: string; ring: string }> = {
  critical: { label: "CRITICAL", color: "#ff6e6e", bg: "rgba(255,110,110,0.12)", ring: "rgba(255,110,110,0.35)" },
  high:     { label: "HIGH",     color: "#ff9500", bg: "rgba(255,149,0,0.12)",   ring: "rgba(255,149,0,0.35)" },
  medium:   { label: "MEDIUM",   color: "#e3b341", bg: "rgba(227,179,65,0.12)",  ring: "rgba(227,179,65,0.35)" },
  low:      { label: "LOW",      color: "#3fb950", bg: "rgba(63,185,80,0.12)",   ring: "rgba(63,185,80,0.35)" },
  info:     { label: "INFO",     color: "#58a6ff", bg: "rgba(88,166,255,0.12)",  ring: "rgba(88,166,255,0.35)" },
};

export function SeverityBadge({ severity, variant = "filled", className }: Props) {
  const key = (severity?.toLowerCase() ?? "info") as Severity;
  const cfg = SEVERITY_CONFIG[key] ?? SEVERITY_CONFIG.info;

  if (variant === "dot") {
    return (
      <span
        className={clsx("inline-block w-2 h-2 rounded-full flex-shrink-0", className)}
        style={{ backgroundColor: cfg.color }}
        title={cfg.label}
      />
    );
  }

  if (variant === "outline") {
    return (
      <span
        className={clsx("inline-flex items-center px-2 py-0.5 rounded text-xs font-medium font-mono", className)}
        style={{ color: cfg.color, border: `1px solid ${cfg.ring}` }}
      >
        {cfg.label}
      </span>
    );
  }

  return (
    <span
      className={clsx("inline-flex items-center px-2 py-0.5 rounded text-xs font-medium font-mono tracking-wide", className)}
      style={{ color: cfg.color, backgroundColor: cfg.bg, border: `1px solid ${cfg.ring}` }}
    >
      {cfg.label}
    </span>
  );
}
