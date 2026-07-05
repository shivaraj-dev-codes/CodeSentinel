import { useParams, Link } from "react-router-dom";
import { useFinding, useSimilarFindings, useUpdateFinding } from "../api/findings";
import { SeverityBadge } from "../components/findings/SeverityBadge";
import { CodeViewer } from "../components/findings/CodeViewer";

export function FindingDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: finding, isLoading } = useFinding(id!);
  const { data: similar } = useSimilarFindings(id!);
  const { mutate: update } = useUpdateFinding();

  if (isLoading) {
    return (
      <div className="p-6 space-y-4 animate-pulse">
        <div className="h-6 bg-bg-elevated rounded w-1/3" />
        <div className="h-40 bg-bg-elevated rounded" />
      </div>
    );
  }

  if (!finding) {
    return (
      <div className="p-6">
        <p className="text-text-secondary">Finding not found.</p>
        <Link to="/findings" className="text-text-link text-sm mt-2 inline-block">← Back to findings</Link>
      </div>
    );
  }

  const getExt = (path: string) => path.split(".").pop() ?? "python";

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <div className="flex items-center gap-2 text-sm text-text-secondary">
        <Link to="/findings" className="hover:text-text-primary">Findings</Link>
        <span>/</span>
        <span className="text-text-primary truncate">{finding.title}</span>
      </div>

      {/* Header */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 flex-wrap">
          <SeverityBadge severity={finding.severity} />
          {finding.owasp_category && <span className="text-xs text-text-muted bg-bg-elevated px-2 py-0.5 rounded">{finding.owasp_category}</span>}
          {finding.cwe_id && <span className="text-xs text-text-muted bg-bg-elevated px-2 py-0.5 rounded font-mono">{finding.cwe_id}</span>}
          <span className={`text-xs ml-auto ${finding.status === "open" ? "text-severity-medium" : "text-status-success"}`}>
            {finding.status.replace("_", " ").toUpperCase()}
          </span>
        </div>
        <h1 className="text-xl font-semibold text-text-primary">{finding.title}</h1>
        <p className="text-sm text-text-secondary leading-relaxed">{finding.description}</p>
      </div>

      {/* Code */}
      <div>
        <div className="text-xs text-severity-critical mb-2">Vulnerable Code — {finding.file_path}:{finding.line_start}</div>
        <CodeViewer code={finding.code_snippet} language={getExt(finding.file_path)} highlightLines={[1, 3]} />
      </div>

      {finding.fix_suggestion && (
        <div>
          <div className="text-xs text-severity-low mb-2">Suggested Fix</div>
          <CodeViewer code={finding.fix_suggestion} language={getExt(finding.file_path)} isFix />
        </div>
      )}

      {/* Metadata */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
        {[
          { label: "Confidence", value: `${Math.round(finding.confidence_score * 100)}%` },
          { label: "Detected By", value: finding.source },
          { label: "Lines", value: `${finding.line_start}–${finding.line_end}` },
          { label: "Category", value: finding.rule.category },
        ].map(({ label, value }) => (
          <div key={label} className="bg-bg-elevated rounded p-3">
            <div className="text-text-muted mb-1">{label}</div>
            <div className="text-text-secondary font-mono">{value}</div>
          </div>
        ))}
      </div>

      {/* Actions */}
      {finding.status === "open" && (
        <div className="flex gap-2">
          {[
            { label: "Mark Resolved", status: "resolved", style: "bg-status-success/10 border border-status-success/30 text-status-success" },
            { label: "Suppress", status: "suppressed", style: "bg-status-warning/10 border border-status-warning/30 text-status-warning" },
            { label: "False Positive", status: "false_positive", style: "bg-bg-elevated border border-border-default text-text-secondary" },
          ].map(({ label, status, style }) => (
            <button key={status} onClick={() => update({ id: finding.id, status })}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors hover:opacity-80 ${style}`}>
              {label}
            </button>
          ))}
        </div>
      )}

      {/* Similar findings */}
      {similar && similar.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-text-secondary mb-3">Similar Findings ({similar.length})</h3>
          <div className="space-y-1">
            {similar.slice(0, 5).map((s) => (
              <Link key={s.id} to={`/findings/${s.id}`}
                className="flex items-center gap-3 px-3 py-2 rounded bg-bg-surface hover:bg-bg-elevated border border-border-muted transition-colors">
                <SeverityBadge severity={s.severity} variant="dot" />
                <span className="text-sm text-text-secondary truncate">{s.title}</span>
                <span className="text-xs text-text-muted font-mono ml-auto">{s.file_path.split("/").slice(-1)[0]}</span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
