import { Link } from "react-router-dom";
import { formatDistanceToNow } from "date-fns";
import type { Repository } from "../../api/repositories";
import { HealthScoreCard } from "../analytics/HealthScoreCard";

interface Props { repo: Repository; }

export function RepositoryCard({ repo }: Props) {
  return (
    <Link to={`/repositories/${repo.id}`}
      className="block bg-bg-surface border border-border-default rounded-lg p-5 hover:bg-bg-elevated hover:border-border-emphasis transition-all group">
      <div className="flex items-start justify-between mb-3">
        <div className="min-w-0 flex-1">
          <h3 className="font-medium text-text-primary group-hover:text-text-link transition-colors truncate">{repo.name}</h3>
          <p className="text-xs text-text-muted font-mono mt-0.5">{repo.full_name}</p>
        </div>
        <HealthScoreCard score={repo.health_score} size={48} />
      </div>

      {repo.description && (
        <p className="text-sm text-text-secondary mb-3 line-clamp-2">{repo.description}</p>
      )}

      <div className="flex items-center gap-3 text-xs text-text-muted">
        {repo.language && <span>{repo.language}</span>}
        <span>{repo.scan_count} scan{repo.scan_count !== 1 ? "s" : ""}</span>
        {repo.open_findings_count > 0 && (
          <span className="text-severity-medium">{repo.open_findings_count} open</span>
        )}
        {repo.last_scanned_at && (
          <span className="ml-auto">{formatDistanceToNow(new Date(repo.last_scanned_at), { addSuffix: true })}</span>
        )}
      </div>
    </Link>
  );
}
