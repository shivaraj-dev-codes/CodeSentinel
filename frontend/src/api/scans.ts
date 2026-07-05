import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";

export interface Scan {
  id: string;
  repository: string;
  repository_name: string;
  triggered_by: string;
  triggered_by_email: string | null;
  commit_sha: string;
  branch: string;
  status: string;
  progress_percent: number;
  is_running: boolean;
  started_at: string;
  completed_at: string | null;
  error_message: string;
  total_findings: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  info_count: number;
  lines_of_code: number;
  files_scanned: number;
  duration_seconds: number | null;
  duration_display: string | null;
}

const scansApi = {
  list: () => api.get<{ success: boolean; data: Scan[] }>("/scans/"),
  get: (id: string) => api.get<{ success: boolean; data: Scan }>(`/scans/${id}/`),
  trigger: (repoId: string, branch: string) =>
    api.post<{ success: boolean; data: Scan }>(`/repositories/${repoId}/scans/`, { branch }),
  cancel: (id: string) => api.post(`/scans/${id}/cancel/`),
};

export function useScans() {
  return useQuery({
    queryKey: ["scans"],
    queryFn: () => scansApi.list().then((r) => r.data.data),
    refetchInterval: (query) => {
      const scans = query.state.data;
      const hasRunning = scans?.some((s) => s.is_running);
      return hasRunning ? 5000 : false;
    },
  });
}

export function useScan(id: string) {
  return useQuery({
    queryKey: ["scans", id],
    queryFn: () => scansApi.get(id).then((r) => r.data.data),
    enabled: !!id,
    refetchInterval: (query) => {
      const scan = query.state.data;
      return scan?.is_running ? 3000 : false;
    },
  });
}

export function useTriggerScan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ repoId, branch }: { repoId: string; branch: string }) =>
      scansApi.trigger(repoId, branch).then((r) => r.data.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["scans"] });
      qc.invalidateQueries({ queryKey: ["repositories"] });
    },
  });
}

export function useCancelScan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => scansApi.cancel(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["scans"] }),
  });
}
