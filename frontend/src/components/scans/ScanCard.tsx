import { Link } from "react-router-dom";
import { formatDistanceToNow } from "date-fns";
import type { Scan } from "../../api/scans";

interface Props { scan: Scan; }

export function ScanCard({ scan }: Props) {
  const statusColor = {
    completed: "text-status-success",
    failed: "text-status-error",
    pending: "text-text-muted",
  }[scan.status] ?? "text-status-running";

  return (
    <Link to={`/scans/${scan.id}`}
      className="block bg-bg-surface border border-border-default rounded-lg p-4 hover:bg-bg-elevated hover:border-border-emphasis transition-all">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-text-primary font-mono">{scan.repository_name}</span>
        <span className={`text-xs font-medium ${statusColor}`}>{scan.status}</span>
      </div>

      <div className="flex items-center gap-3 text-xs text-text-muted mb-3">
        <span className="font-mono">{scan.branch}</span>
        <span>·</span>
        <span className="font-mono">{scan.commit_sha.slice(0, 7)}</span>
        {scan.duration_display && <><span>·</span><span>{scan.duration_display}</span></>}
      </div>

      {scan.total_findings > 0 && (
        <div className="flex items-center gap-2">
          {scan.critical_count > 0 && <span className="text-xs font-mono text-severity-critical">{scan.critical_count} critical</span>}
          {scan.high_count > 0 && <span className="text-xs font-mono text-severity-high">{scan.high_count} high</span>}
          {scan.medium_count > 0 && <span className="text-xs font-mono text-severity-medium">{scan.medium_count} medium</span>}
          {scan.low_count > 0 && <span className="text-xs font-mono text-severity-low">{scan.low_count} low</span>}
        </div>
      )}

      <div className="text-xs text-text-muted mt-2">
        {formatDistanceToNow(new Date(scan.started_at), { addSuffix: true })}
      </div>
    </Link>
  );
}
