import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";

export interface Rule {
  id: string;
  rule_id_slug: string;
  name: string;
  category: string;
  severity: string;
  owasp_category: string;
  cwe_id: string;
  language: string;
}

export interface Finding {
  id: string;
  scan: string;
  rule: Rule;
  repository_name: string;
  scan_branch: string;
  file_path: string;
  line_start: number;
  line_end: number;
  column_start: number | null;
  column_end: number | null;
  severity: string;
  title: string;
  description: string;
  fix_suggestion: string;
  code_snippet: string;
  confidence_score: number;
  source: string;
  owasp_category: string;
  cwe_id: string;
  status: string;
  suppressed_reason: string;
  suppressed_by_email: string | null;
  suppressed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface FindingListItem {
  id: string;
  scan: string;
  file_path: string;
  line_start: number;
  line_end: number;
  severity: string;
  title: string;
  rule_name: string;
  rule_category: string;
  cwe_id: string;
  confidence_score: number;
  source: string;
  status: string;
  created_at: string;
}

export interface FindingsFilters {
  severity?: string;
  status?: string;
  category?: string;
  file_path?: string;
  scan_id?: string;
  source?: string;
}

const findingsApi = {
  list: (filters?: FindingsFilters) =>
    api.get<{ success: boolean; data: FindingListItem[]; meta: { total: number } }>("/findings/", { params: filters }),
  get: (id: string) =>
    api.get<{ success: boolean; data: Finding }>(`/findings/${id}/`),
  update: (id: string, payload: { status: string; suppressed_reason?: string }) =>
    api.patch<{ success: boolean; data: Finding }>(`/findings/${id}/`, payload),
  similar: (id: string) =>
    api.get<{ success: boolean; data: FindingListItem[] }>(`/findings/${id}/similar/`),
};

export function useFindings(filters?: FindingsFilters) {
  return useQuery({
    queryKey: ["findings", filters],
    queryFn: () => findingsApi.list(filters).then((r) => r.data),
  });
}

export function useFinding(id: string) {
  return useQuery({
    queryKey: ["findings", id],
    queryFn: () => findingsApi.get(id).then((r) => r.data.data),
    enabled: !!id,
  });
}

export function useUpdateFinding() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: string; status: string; suppressed_reason?: string }) =>
      findingsApi.update(id, payload).then((r) => r.data.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["findings"] });
    },
  });
}

export function useSimilarFindings(id: string) {
  return useQuery({
    queryKey: ["findings", id, "similar"],
    queryFn: () => findingsApi.similar(id).then((r) => r.data.data),
    enabled: !!id,
  });
}
