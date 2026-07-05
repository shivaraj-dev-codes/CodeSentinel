import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { formatDistanceToNow } from "date-fns";
import { useOverviewStats, useSeverityTrend } from "../api/analytics";
import { useScans } from "../api/scans";
import { SeverityBadge } from "../components/findings/SeverityBadge";
import { SeverityTrendChart } from "../components/analytics/SeverityTrendChart";
import { CategoryDonut } from "../components/analytics/CategoryDonut";

function StatCard({ label, value, delta, className }: { label: string; value: number | string | null; delta?: number | null; className?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-bg-surface border border-border-default rounded-lg p-5 ${className ?? ""}`}
    >
      <div className="text-sm text-text-secondary mb-2">{label}</div>
      <div className="text-2xl font-bold text-text-primary font-mono">
        {value ?? "—"}
      </div>
      {delta !== undefined && delta !== null && (
        <div className={`text-xs mt-1 ${delta > 0 ? "text-status-error" : delta < 0 ? "text-status-success" : "text-text-muted"}`}>
          {delta > 0 ? `+${delta}` : delta} since yesterday
        </div>
      )}
    </motion.div>
  );
}

function ScanStatusBadge({ status }: { status: string }) {
  const cfg: Record<string, { label: string; color: string; pulse?: boolean }> = {
    pending:    { label: "Pending",    color: "text-text-muted" },
    cloning:    { label: "Running",    color: "text-status-running", pulse: true },
    analyzing:  { label: "Analyzing", color: "text-status-running", pulse: true },
    running_ml: { label: "ML Phase",  color: "text-status-running", pulse: true },
    aggregating:{ label: "Scoring",   color: "text-status-running", pulse: true },
    completed:  { label: "Completed", color: "text-status-success" },
    failed:     { label: "Failed",    color: "text-status-error" },
  };
  const c = cfg[status] ?? cfg.pending;
  return (
    <span className={`flex items-center gap-1.5 text-xs font-medium ${c.color}`}>
      {c.pulse && <span className="w-1.5 h-1.5 rounded-full bg-status-running pulse-ring" />}
      {!c.pulse && <span className="w-1.5 h-1.5 rounded-full bg-current" />}
      {c.label}
    </span>
  );
}

export function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useOverviewStats();
  const { data: scans } = useScans();

  const recentScans = scans?.slice(0, 8) ?? [];

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-text-primary">Dashboard</h1>
        <p className="text-sm text-text-secondary mt-0.5">Security overview across all connected repositories</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard label="Open Findings" value={statsLoading ? "…" : stats?.total_open_findings ?? 0} delta={stats?.open_findings_delta} />
        <StatCard label="Critical Issues" value={statsLoading ? "…" : stats?.critical_issues ?? 0} />
        <StatCard label="Repos Connected" value={statsLoading ? "…" : stats?.repos_connected ?? 0} />
        <StatCard label="Scans This Week" value={statsLoading ? "…" : stats?.scans_this_week ?? 0} />
      </div>

      {/* Recent scans + donut */}
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
        {/* Recent scans table */}
        <div className="xl:col-span-3 bg-bg-surface border border-border-default rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-border-default flex items-center justify-between">
            <span className="text-sm font-medium text-text-primary">Recent Scans</span>
            <Link to="/scans" className="text-xs text-text-link hover:underline">View all</Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-muted">
                  {["Repository", "Branch", "Status", "Findings", "Duration", "Time"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-left text-xs text-text-muted font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {recentScans.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-text-muted text-sm">
                      No scans yet. Trigger your first scan from a repository page.
                    </td>
                  </tr>
                ) : (
                  recentScans.map((scan) => (
                    <tr key={scan.id}
                      className="border-b border-border-muted last:border-0 hover:bg-bg-elevated transition-colors row-transition cursor-pointer">
                      <td className="px-4 py-3">
                        <Link to={`/scans/${scan.id}`} className="text-text-link hover:underline font-mono text-xs">
                          {scan.repository_name}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-text-secondary font-mono text-xs">{scan.branch}</td>
                      <td className="px-4 py-3"><ScanStatusBadge status={scan.status} /></td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          {scan.critical_count > 0 && <span className="text-severity-critical text-xs font-mono">{scan.critical_count}C</span>}
                          {scan.high_count > 0 && <span className="text-severity-high text-xs font-mono">{scan.high_count}H</span>}
                          {scan.medium_count > 0 && <span className="text-severity-medium text-xs font-mono">{scan.medium_count}M</span>}
                          {scan.low_count > 0 && <span className="text-severity-low text-xs font-mono">{scan.low_count}L</span>}
                          {scan.total_findings === 0 && <span className="text-text-muted text-xs">—</span>}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-text-secondary text-xs font-mono">{scan.duration_display ?? "—"}</td>
                      <td className="px-4 py-3 text-text-muted text-xs">
                        {formatDistanceToNow(new Date(scan.started_at), { addSuffix: true })}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Donut chart */}
        <div className="xl:col-span-2">
          <CategoryDonut />
        </div>
      </div>

      {/* Trend chart */}
      <div className="bg-bg-surface border border-border-default rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-medium text-text-primary">Vulnerability Trend (30 days)</span>
        </div>
        <SeverityTrendChart days={30} />
      </div>
    </div>
  );
}
