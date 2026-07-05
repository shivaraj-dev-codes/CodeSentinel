import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { formatDistanceToNow } from "date-fns";
import { useRepository } from "../api/repositories";
import { useScans, useTriggerScan } from "../api/scans";
import { SeverityBadge } from "../components/findings/SeverityBadge";

export function RepositoryDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: repo, isLoading } = useRepository(id!);
  const { data: allScans } = useScans();
  const { mutate: triggerScan, isPending: isTriggering } = useTriggerScan();

  const [branch, setBranch] = useState("");
  const [activeTab, setActiveTab] = useState<"overview" | "scans" | "findings">("overview");

  const repoScans = allScans?.filter((s) => s.repository === id) ?? [];

  const handleTrigger = () => {
    if (!id) return;
    triggerScan({ repoId: id, branch: branch || (repo?.default_branch ?? "main") });
  };

  if (isLoading) {
    return (
      <div className="p-6 space-y-4 animate-pulse">
        <div className="h-6 bg-bg-elevated rounded w-1/3" />
        <div className="h-4 bg-bg-elevated rounded w-1/4" />
      </div>
    );
  }

  if (!repo) {
    return (
      <div className="p-6">
        <p className="text-text-secondary">Repository not found.</p>
        <Link to="/repositories" className="text-text-link text-sm mt-2 inline-block">← Back to repositories</Link>
      </div>
    );
  }

  const healthColor = repo.health_score < 40 ? "#ff6e6e" : repo.health_score < 70 ? "#e3b341" : "#3fb950";

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link to="/repositories" className="text-text-muted hover:text-text-secondary text-sm">Repositories</Link>
            <span className="text-text-muted">/</span>
            <span className="text-text-primary font-medium">{repo.name}</span>
          </div>
          <div className="flex items-center gap-3 text-sm text-text-secondary">
            <a href={repo.github_repo_url} target="_blank" rel="noopener noreferrer" className="text-text-link hover:underline font-mono">{repo.full_name}</a>
            <span>·</span>
            <span>branch: <code className="font-mono">{repo.default_branch}</code></span>
            {repo.last_scanned_at && (
              <>
                <span>·</span>
                <span>scanned {formatDistanceToNow(new Date(repo.last_scanned_at), { addSuffix: true })}</span>
              </>
            )}
          </div>
        </div>

        {/* Health score + trigger */}
        <div className="flex items-center gap-4">
          <div className="flex flex-col items-center">
            <svg viewBox="0 0 36 36" className="w-16 h-16">
              <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none" stroke="#30363d" strokeWidth="3" />
              <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none" stroke={healthColor} strokeWidth="3"
                strokeDasharray={`${repo.health_score}, 100`} strokeLinecap="round" />
              <text x="18" y="20.35" className="font-mono font-bold" fontSize="9" textAnchor="middle" fill={healthColor}>{repo.health_score}</text>
            </svg>
            <span className="text-xs text-text-muted">Health</span>
          </div>

          <div className="space-y-2">
            <input value={branch} onChange={(e) => setBranch(e.target.value)}
              placeholder={repo.default_branch}
              className="w-36 bg-bg-elevated border border-border-default rounded px-2 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-primary" />
            <button onClick={handleTrigger} disabled={isTriggering}
              className="w-full px-3 py-1.5 rounded bg-accent-primary hover:bg-accent-hover text-white text-sm font-medium transition-colors disabled:opacity-50">
              {isTriggering ? "Triggering…" : "Trigger Scan"}
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border-default gap-4">
        {(["overview", "scans", "findings"] as const).map((tab) => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`pb-2 text-sm capitalize transition-colors border-b-2 ${activeTab === tab ? "border-accent-primary text-text-primary" : "border-transparent text-text-secondary hover:text-text-primary"}`}>
            {tab}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "scans" && (
        <div className="bg-bg-surface border border-border-default rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-border-muted">
              {["Branch", "Status", "Critical", "High", "Medium", "Low", "Duration", "Triggered"].map((h) => (
                <th key={h} className="px-4 py-2.5 text-left text-xs text-text-muted font-medium">{h}</th>
              ))}
            </tr></thead>
            <tbody>
              {repoScans.length === 0 ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center text-text-muted">No scans yet.</td></tr>
              ) : repoScans.map((scan) => (
                <tr key={scan.id} className="border-b border-border-muted last:border-0 hover:bg-bg-elevated cursor-pointer row-transition">
                  <td className="px-4 py-3 font-mono text-xs text-text-secondary">{scan.branch}</td>
                  <td className="px-4 py-3"><Link to={`/scans/${scan.id}`} className="text-text-link hover:underline">{scan.status}</Link></td>
                  <td className="px-4 py-3 text-severity-critical font-mono text-xs">{scan.critical_count || "—"}</td>
                  <td className="px-4 py-3 text-severity-high font-mono text-xs">{scan.high_count || "—"}</td>
                  <td className="px-4 py-3 text-severity-medium font-mono text-xs">{scan.medium_count || "—"}</td>
                  <td className="px-4 py-3 text-severity-low font-mono text-xs">{scan.low_count || "—"}</td>
                  <td className="px-4 py-3 text-text-secondary text-xs">{scan.duration_display ?? "—"}</td>
                  <td className="px-4 py-3 text-text-muted text-xs">{formatDistanceToNow(new Date(scan.started_at), { addSuffix: true })}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === "overview" && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Open Findings", value: repo.open_findings_count },
            { label: "Total Scans", value: repo.scan_count },
            { label: "Health Score", value: repo.health_score },
            { label: "Default Branch", value: repo.default_branch },
          ].map(({ label, value }) => (
            <div key={label} className="bg-bg-surface border border-border-default rounded-lg p-4">
              <div className="text-xs text-text-muted mb-1">{label}</div>
              <div className="text-lg font-bold text-text-primary font-mono">{value}</div>
            </div>
          ))}
        </div>
      )}

      {activeTab === "findings" && (
        <div className="text-center py-8 text-text-secondary">
          <Link to={`/findings?repo=${id}`} className="text-text-link hover:underline">
            View all findings for {repo.name} →
          </Link>
        </div>
      )}
    </div>
  );
}
