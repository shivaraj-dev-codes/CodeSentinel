import { clsx } from "clsx";
import { motion } from "framer-motion";

const STAGES = [
  { key: "pending",     label: "Queued" },
  { key: "cloning",     label: "Fetching Repo" },
  { key: "analyzing",   label: "Static Analysis" },
  { key: "running_ml",  label: "ML Detection" },
  { key: "aggregating", label: "Aggregating" },
  { key: "completed",   label: "Complete" },
];

interface Props {
  percent: number;
  status: string;
  message: string;
  totalFindings?: number;
}

export function ScanProgress({ percent, status, message, totalFindings }: Props) {
  const currentIndex = STAGES.findIndex((s) => s.key === status);
  const failed = status === "failed";

  return (
    <div className="bg-bg-surface border border-border-default rounded-lg p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {!failed && status !== "completed" && (
            <span className="w-2 h-2 rounded-full bg-status-running pulse-ring" />
          )}
          {status === "completed" && <span className="w-2 h-2 rounded-full bg-status-success" />}
          {failed && <span className="w-2 h-2 rounded-full bg-status-error" />}
          <span className="text-sm font-medium text-text-primary">
            {failed ? "Scan Failed" : status === "completed" ? "Scan Complete" : "Scan Running"}
          </span>
        </div>
        <span className="text-sm text-text-secondary font-mono">{percent}%</span>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-bg-elevated rounded-full h-1.5 overflow-hidden">
        <motion.div
          className={clsx(
            "h-full rounded-full",
            failed ? "bg-status-error" : percent < 100 ? "progress-shimmer" : "bg-status-success"
          )}
          initial={{ width: 0 }}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>

      {/* Stages */}
      <div className="flex items-center gap-1 overflow-x-auto">
        {STAGES.map((stage, i) => {
          const done = currentIndex > i || status === "completed";
          const active = currentIndex === i && !failed;
          return (
            <div key={stage.key} className="flex items-center gap-1 flex-shrink-0">
              <div className={clsx(
                "flex items-center gap-1 px-2 py-1 rounded text-xs",
                done && !active ? "text-status-success" :
                active ? "text-status-running" :
                "text-text-muted"
              )}>
                {done && !active ? "✓ " : active ? "⟳ " : "○ "}
                {stage.label}
              </div>
              {i < STAGES.length - 1 && (
                <span className="text-text-muted">→</span>
              )}
            </div>
          );
        })}
      </div>

      {/* Status message */}
      {message && (
        <p className="text-sm text-text-secondary font-mono">
          {totalFindings !== undefined && totalFindings > 0 && (
            <span className="text-severity-medium mr-2">{totalFindings} findings found so far…</span>
          )}
          {message}
        </p>
      )}
    </div>
  );
}
