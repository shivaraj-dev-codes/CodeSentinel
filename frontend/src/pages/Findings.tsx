import { useState } from "react";
import { Link } from "react-router-dom";
import { useFindings } from "../api/findings";
import { SeverityBadge } from "../components/findings/SeverityBadge";
import { useDebounce } from "../hooks/useDebounce";

export function Findings() {
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("open");
  const [fileSearch, setFileSearch] = useState("");
  const debouncedFile = useDebounce(fileSearch);

  const { data, isLoading } = useFindings({
    ...(severity ? { severity } : {}),
    ...(status ? { status } : {}),
    ...(debouncedFile ? { file_path: debouncedFile } : {}),
  });

  const findings = data?.data ?? [];
  const total = data?.meta?.total ?? 0;

  return (
    <div className="p-6 space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-text-primary">All Findings</h1>
        <p className="text-sm text-text-secondary mt-0.5">{total} finding{total !== 1 ? "s" : ""} across all repositories</p>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <input value={fileSearch} onChange={(e) => setFileSearch(e.target.value)}
          placeholder="Filter by file path…"
          className="bg-bg-elevated border border-border-default rounded px-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-primary w-64" />
        <select value={severity} onChange={(e) => setSeverity(e.target.value)}
          className="bg-bg-elevated border border-border-default rounded px-3 py-1.5 text-sm text-text-secondary focus:outline-none focus:border-accent-primary">
          <option value="">All severities</option>
          {["critical", "high", "medium", "low", "info"].map((s) => (
            <option key={s} value={s}>{s.toUpperCase()}</option>
          ))}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)}
          className="bg-bg-elevated border border-border-default rounded px-3 py-1.5 text-sm text-text-secondary focus:outline-none focus:border-accent-primary">
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="resolved">Resolved</option>
          <option value="suppressed">Suppressed</option>
          <option value="false_positive">False Positive</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-bg-surface border border-border-default rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-muted">
              {["Severity", "Title", "File", "Repository", "Confidence", "Source", "Status"].map((h) => (
                <th key={h} className="px-4 py-2.5 text-left text-xs text-text-muted font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              [1,2,3,4,5,6].map(i => (
                <tr key={i} className="border-b border-border-muted">
                  {[1,2,3,4,5,6,7].map(j => (
                    <td key={j} className="px-4 py-3"><div className="h-3 bg-bg-elevated rounded animate-pulse" /></td>
                  ))}
                </tr>
              ))
            ) : findings.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-text-muted">
                  No findings match the current filters.
                </td>
              </tr>
            ) : (
              findings.map((f) => (
                <tr key={f.id} className="border-b border-border-muted last:border-0 hover:bg-bg-elevated transition-colors row-transition">
                  <td className="px-4 py-3"><SeverityBadge severity={f.severity} variant="outline" /></td>
                  <td className="px-4 py-3">
                    <Link to={`/findings/${f.id}`} className="text-text-link hover:underline">{f.title}</Link>
                    <div className="text-xs text-text-muted mt-0.5">{f.rule_category}</div>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-text-secondary">
                    {f.file_path.split("/").slice(-2).join("/")}:{f.line_start}
                  </td>
                  <td className="px-4 py-3 text-text-secondary text-xs">—</td>
                  <td className="px-4 py-3 text-text-secondary font-mono text-xs">{Math.round(f.confidence_score * 100)}%</td>
                  <td className="px-4 py-3 text-text-muted text-xs">{f.source}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium ${f.status === "open" ? "text-severity-medium" : "text-status-success"}`}>
                      {f.status.replace("_", " ")}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
