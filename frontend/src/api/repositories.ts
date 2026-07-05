import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";

export interface Repository {
  id: string;
  name: string;
  full_name: string;
  github_repo_url: string;
  clone_url: string;
  default_branch: string;
  description: string;
  is_private: boolean;
  language: string;
  health_score: number;
  scan_count: number;
  open_findings_count: number;
  last_scanned_at: string | null;
  created_at: string;
}

export interface GitHubRepo {
  id: number;
  name: string;
  full_name: string;
  html_url: string;
  clone_url: string;
  default_branch: string;
  description: string | null;
  private: boolean;
  language: string | null;
  already_connected: boolean;
}

const reposApi = {
  list: () => api.get<{ success: boolean; data: Repository[] }>("/repositories/"),
  get: (id: string) => api.get<{ success: boolean; data: Repository }>(`/repositories/${id}/`),
  add: (fullName: string) => api.post<{ success: boolean; data: Repository }>("/repositories/", { full_name: fullName }),
  remove: (id: string) => api.delete(`/repositories/${id}/`),
  listGitHub: () => api.get<{ success: boolean; data: GitHubRepo[] }>("/repositories/github/"),
};

export function useRepositories() {
  return useQuery({
    queryKey: ["repositories"],
    queryFn: () => reposApi.list().then((r) => r.data.data),
  });
}

export function useRepository(id: string) {
  return useQuery({
    queryKey: ["repositories", id],
    queryFn: () => reposApi.get(id).then((r) => r.data.data),
    enabled: !!id,
  });
}

export function useGitHubRepos() {
  return useQuery({
    queryKey: ["github-repos"],
    queryFn: () => reposApi.listGitHub().then((r) => r.data.data),
  });
}

export function useAddRepository() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (fullName: string) => reposApi.add(fullName).then((r) => r.data.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["repositories"] }),
  });
}

export function useRemoveRepository() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => reposApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["repositories"] }),
  });
}
