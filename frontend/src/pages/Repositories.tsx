import { useState } from "react";
import { Link } from "react-router-dom";
import { useRepositories } from "../api/repositories";

export function Repositories() {
  const { data: repos, isLoading } = useRepositories();

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-text-primary">Repositories</h1>
          <p className="text-sm text-text-secondary mt-0.5">
            {repos?.length ?? 0} repository{repos?.length !== 1 ? "ies" : "y"} connected
          </p>
        </div>
        <Link to="/settings" className="px-3 py-1.5 rounded-md bg-accent-primary hover:bg-accent-hover text-white text-sm font-medium transition-colors">
          Connect Repository
        </Link>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-bg-surface border border-border-default rounded-lg p-5 animate-pulse">
              <div className="h-4 bg-bg-elevated rounded w-2/3 mb-3" />
              <div className="h-3 bg-bg-elevated rounded w-1/3 mb-6" />
              <div className="h-8 bg-bg-elevated rounded" />
            </div>
          ))}
        </div>
      ) : repos?.length === 0 ? (
        <div className="border border-border-default rounded-lg p-12 text-center">
          <div className="text-text-muted mb-3">
            <svg viewBox="0 0 24 24" className="w-10 h-10 mx-auto mb-4" fill="none" stroke="currentColor" strokeWidth={1.5}>
              <path d="M3 3h6v18H3zM15 3h6v18h-6zM9 12h6"/>
            </svg>
          </div>
          <h3 className="text-text-primary font-medium mb-1">No repositories connected yet</h3>
          <p className="text-sm text-text-secondary mb-4">
            Connect your first GitHub repository to start scanning for vulnerabilities.
          </p>
          <Link to="/settings" className="px-4 py-2 rounded-md bg-accent-primary hover:bg-accent-hover text-white text-sm font-medium transition-colors">
            Connect GitHub Repository
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {repos?.map((repo) => (
            <Link key={repo.id} to={`/repositories/${repo.id}`}
              className="bg-bg-surface border border-border-default rounded-lg p-5 hover:bg-bg-elevated hover:border-border-emphasis transition-all group">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-medium text-text-primary group-hover:text-text-link transition-colors">{repo.name}</h3>
                  <p className="text-xs text-text-muted font-mono">{repo.full_name}</p>
                </div>
                <HealthBadge score={repo.health_score} />
              </div>
              {repo.description && (
                <p className="text-sm text-text-secondary mb-4 line-clamp-2">{repo.description}</p>
              )}
              <div className="flex items-center gap-4 text-xs text-text-muted">
                {repo.language && <span>{repo.language}</span>}
                <span>{repo.scan_count} scan{repo.scan_count !== 1 ? "s" : ""}</span>
                <span>{repo.open_findings_count} open finding{repo.open_findings_count !== 1 ? "s" : ""}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function HealthBadge({ score }: { score: number }) {
  const color = score < 40 ? "#ff6e6e" : score < 70 ? "#e3b341" : "#3fb950";
  return (
    <div className="flex items-center gap-1.5 flex-shrink-0">
      <div className="w-8 h-8 rounded-full border-2 flex items-center justify-center text-xs font-bold font-mono"
        style={{ borderColor: color, color }}>
        {score}
      </div>
    </div>
  );
}
