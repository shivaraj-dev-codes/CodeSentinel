import { useState } from "react";
import { useAuthStore } from "../store/authStore";
import { useGitHubRepos, useAddRepository, useRemoveRepository } from "../api/repositories";
import { useRepositories } from "../api/repositories";

export function Settings() {
  const user = useAuthStore((s) => s.user);
  const { data: githubRepos, isLoading: loadingGH, refetch } = useGitHubRepos();
  const { data: connected } = useRepositories();
  const { mutate: addRepo } = useAddRepository();
  const { mutate: removeRepo } = useRemoveRepository();
  const [adding, setAdding] = useState<string | null>(null);

  const connectedIds = new Set(connected?.map((r) => r.github_repo_id?.toString()) ?? []);

  const handleAdd = (fullName: string) => {
    setAdding(fullName);
    addRepo(fullName, { onSettled: () => { setAdding(null); refetch(); } });
  };

  return (
    <div className="p-6 space-y-8 max-w-3xl">
      <div>
        <h1 className="text-xl font-semibold text-text-primary">Settings</h1>
        <p className="text-sm text-text-secondary mt-0.5">Manage your account and connected repositories</p>
      </div>

      {/* Profile */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-text-primary border-b border-border-default pb-2">Profile</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-text-muted mb-1">Email</div>
            <div className="text-text-primary">{user?.email}</div>
          </div>
          <div>
            <div className="text-text-muted mb-1">Full Name</div>
            <div className="text-text-primary">{user?.full_name || "—"}</div>
          </div>
          <div>
            <div className="text-text-muted mb-1">GitHub Account</div>
            <div className="text-text-primary">
              {user?.github_username ? (
                <a href={`https://github.com/${user.github_username}`} target="_blank" rel="noopener noreferrer"
                  className="text-text-link hover:underline">@{user.github_username}</a>
              ) : (
                <span className="text-text-muted">Not connected</span>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* GitHub Repos */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-text-primary border-b border-border-default pb-2">
          GitHub Repositories
        </h2>

        {!user?.has_github_connected ? (
          <div className="text-center py-8 border border-border-default rounded-lg">
            <p className="text-sm text-text-secondary mb-4">Connect your GitHub account to manage repositories.</p>
            <a
              href={`https://github.com/login/oauth/authorize?client_id=${import.meta.env.VITE_GITHUB_CLIENT_ID}&scope=repo`}
              className="px-4 py-2 rounded-md bg-accent-primary hover:bg-accent-hover text-white text-sm font-medium transition-colors inline-block">
              Connect GitHub
            </a>
          </div>
        ) : loadingGH ? (
          <div className="space-y-2">
            {[1,2,3,4].map(i => <div key={i} className="h-12 bg-bg-elevated rounded animate-pulse" />)}
          </div>
        ) : (
          <div className="space-y-1">
            {(githubRepos ?? []).map((repo) => {
              const isConnected = repo.already_connected || connectedIds.has(repo.id.toString());
              const isAdding = adding === repo.full_name;
              return (
                <div key={repo.id} className="flex items-center gap-3 px-3 py-2.5 bg-bg-surface border border-border-muted rounded hover:bg-bg-elevated transition-colors">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-text-primary font-medium truncate">{repo.full_name}</div>
                    <div className="flex items-center gap-2 text-xs text-text-muted">
                      {repo.language && <span>{repo.language}</span>}
                      {repo.private && <span>Private</span>}
                    </div>
                  </div>
                  {isConnected ? (
                    <span className="text-xs text-status-success bg-status-success/10 border border-status-success/20 px-2 py-0.5 rounded">
                      Connected
                    </span>
                  ) : (
                    <button onClick={() => handleAdd(repo.full_name)} disabled={isAdding}
                      className="text-xs px-3 py-1 rounded bg-accent-primary hover:bg-accent-hover text-white transition-colors disabled:opacity-50">
                      {isAdding ? "Adding…" : "Add"}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
