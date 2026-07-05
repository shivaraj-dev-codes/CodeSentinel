import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useScan } from "../api/scans";
import { useFindings, useFinding, useUpdateFinding, type FindingListItem } from "../api/findings";
import { useScanWebSocket } from "../hooks/useScanWebSocket";
import { useScanStore } from "../store/scanStore";
import { SeverityBadge } from "../components/findings/SeverityBadge";
import { ScanProgress } from "../components/scans/ScanProgress";
import { CodeViewer } from "../components/findings/CodeViewer";
import { useDebounce } from "../hooks/useDebounce";

export function ScanDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: scan } = useScan(id!);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("open");
  const [fileSearch, setFileSearch] = useState("");
  const debouncedFile = useDebounce(fileSearch, 300);

  const progress = useScanStore((s) => s.progress[id!]);
  useScanWebSocket(scan?.is_running ? id! : null, scan?.is_running);

  const { data: findingsData, isLoading } = useFindings({
    scan_id: id,
    ...(severityFilter ? { severity: severityFilter } : {}),
    ...(statusFilter ? { status: statusFilter } : {}),
    ...(debouncedFile ? { file_path: debouncedFile } : {}),
  });

  const { data: selected } = useFinding(selectedId ?? "");
  const { mutate: updateFinding } = useUpdateFinding();

  const findings = findingsData?.data ?? [];

  const getFileExt = (path: string) => path.split(".").pop() ?? "python";

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border-default bg-bg-surface flex items-center gap-3 flex-shrink-0">
        <Link to={`/repositories/${scan?.repository}`} className="text-text-muted hover:text-text-secondary text-sm">Repositories</Link>
        <span className="text-text-muted">/</span>
        <span className="text-text-secondary text-sm font-mono">{scan?.repository_name}</span>
        <span className="text-text-muted">/</span>
        <span className="text-text-primary text-sm">Scan</span>
        {scan?.commit_sha && (
          <code className="text-xs text-text-muted bg-bg-elevated px-1.5 py-0.5 rounded font-mono">{scan.commit_sha.slice(0, 7)}</code>
        )}
      </div>

      {/* Live progress bar (when running) */}
      {scan?.is_running && (
        <div className="px-6 py-4 border-b border-border-default flex-shrink-0">
          <ScanProgress
            percent={progress?.percent ?? scan.progress_percent}
            status={progress?.status ?? scan.status}
            message={progress?.message ?? ""}
            totalFindings={findings.length}
          />
        </div>
      )}

      {/* Split pane */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left — findings list */}
        <div className="w-96 flex-shrink-0 flex flex-col border-r border-border-default overflow-hidden">
          {/* Filters */}
          <div className="p-3 border-b border-border-default space-y-2">
            <input value={fileSearch} onChange={(e) => setFileSearch(e.target.value)}
              placeholder="Filter by file path…"
              className="w-full bg-bg-elevated border border-border-default rounded px-2.5 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-primary" />
            <div className="flex gap-2">
              <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}
                className="flex-1 bg-bg-elevated border border-border-default rounded px-2 py-1.5 text-sm text-text-secondary focus:outline-none focus:border-accent-primary">
                <option value="">All severities</option>
                {["critical", "high", "medium", "low", "info"].map((s) => (
                  <option key={s} value={s}>{s.toUpperCase()}</option>
                ))}
              </select>
              <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
                className="flex-1 bg-bg-elevated border border-border-default rounded px-2 py-1.5 text-sm text-text-secondary focus:outline-none focus:border-accent-primary">
                <option value="">All statuses</option>
                <option value="open">Open</option>
                <option value="resolved">Resolved</option>
                <option value="suppressed">Suppressed</option>
                <option value="false_positive">False Positive</option>
              </select>
            </div>
          </div>

          {/* Findings list */}
          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <div className="p-4 space-y-2">
                {[1,2,3,4,5].map(i => <div key={i} className="h-12 bg-bg-elevated rounded animate-pulse" />)}
              </div>
            ) : findings.length === 0 ? (
              <div className="p-6 text-center text-text-muted text-sm">
                {scan?.is_running ? "Waiting for findings…" : "No findings match the current filters."}
              </div>
            ) : (
              findings.map((f) => (
                <button key={f.id} onClick={() => setSelectedId(f.id)}
                  className={`w-full text-left px-4 py-3 border-b border-border-muted hover:bg-bg-elevated transition-colors row-transition ${selectedId === f.id ? "bg-bg-elevated border-l-2 border-l-accent-primary" : ""}`}>
                  <div className="flex items-center gap-2 mb-1">
                    <SeverityBadge severity={f.severity} variant="dot" />
                    <span className="text-sm text-text-primary truncate">{f.title}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-text-muted font-mono">
                    <span className="truncate">{f.file_path.split("/").slice(-2).join("/")}</span>
                    <span>:{f.line_start}</span>
                    <span className="ml-auto">{Math.round(f.confidence_score * 100)}%</span>
                  </div>
                </button>
              ))
            )}
          </div>

          <div className="px-4 py-2 border-t border-border-default text-xs text-text-muted">
            {findings.length} finding{findings.length !== 1 ? "s" : ""}
          </div>
        </div>

        {/* Right — finding detail */}
        <div className="flex-1 overflow-y-auto">
          {!selected ? (
            <div className="flex items-center justify-center h-full text-text-muted">
              <div className="text-center">
                <p className="text-sm">Select a finding to view details</p>
              </div>
            </div>
          ) : (
            <div className="p-6 space-y-6">
              {/* Finding header */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <SeverityBadge severity={selected.severity} />
                  {selected.owasp_category && (
                    <span className="text-xs text-text-muted bg-bg-elevated px-2 py-0.5 rounded">{selected.owasp_category}</span>
                  )}
                  {selected.cwe_id && (
                    <span className="text-xs text-text-muted bg-bg-elevated px-2 py-0.5 rounded font-mono">{selected.cwe_id}</span>
                  )}
                  <span className={`text-xs ml-auto ${selected.status === "open" ? "text-severity-medium" : "text-status-success"}`}>
                    {selected.status.replace("_", " ").toUpperCase()}
                  </span>
                </div>
                <h2 className="text-lg font-semibold text-text-primary">{selected.title}</h2>
                <p className="text-sm text-text-secondary leading-relaxed">{selected.description}</p>
              </div>

              {/* Vulnerable code */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-medium text-severity-critical">Vulnerable Code</span>
                  <code className="text-xs text-text-muted font-mono">{selected.file_path}:{selected.line_start}</code>
                </div>
                <CodeViewer
                  code={selected.code_snippet}
                  language={getFileExt(selected.file_path)}
                  highlightLines={[1, selected.line_end - selected.line_start + 1]}
                  isFix={false}
                />
              </div>

              {/* Fix suggestion */}
              {selected.fix_suggestion && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-medium text-severity-low">Suggested Fix</span>
                  </div>
                  <CodeViewer code={selected.fix_suggestion} language={getFileExt(selected.file_path)} isFix={true} />
                </div>
              )}

              {/* Metadata */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                {[
                  { label: "Confidence", value: `${Math.round(selected.confidence_score * 100)}%` },
                  { label: "Detected By", value: selected.source },
                  { label: "Lines", value: `${selected.line_start}–${selected.line_end}` },
                  { label: "Rule", value: selected.rule.rule_id_slug },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-bg-elevated rounded p-3">
                    <div className="text-text-muted mb-1">{label}</div>
                    <div className="text-text-secondary font-mono">{value}</div>
                  </div>
                ))}
              </div>

              {/* Action buttons */}
              {selected.status === "open" && (
                <div className="flex items-center gap-2">
                  {[
                    { label: "Mark Resolved", status: "resolved", color: "bg-status-success/10 border-status-success/30 text-status-success hover:bg-status-success/20" },
                    { label: "Suppress", status: "suppressed", color: "bg-status-warning/10 border-status-warning/30 text-status-warning hover:bg-status-warning/20" },
                    { label: "False Positive", status: "false_positive", color: "bg-text-muted/10 border-border-default text-text-secondary hover:bg-bg-elevated" },
                  ].map(({ label, status, color }) => (
                    <button key={status}
                      onClick={() => updateFinding({ id: selected.id, status })}
                      className={`px-3 py-1.5 rounded border text-sm font-medium transition-colors ${color}`}>
                      {label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
