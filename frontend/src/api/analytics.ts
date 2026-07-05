import { useQuery } from "@tanstack/react-query";
import { api } from "./client";

export interface OverviewStats {
  total_open_findings: number;
  open_findings_delta: number;
  critical_issues: number;
  repos_connected: number;
  scans_this_week: number;
  scans_last_week: number;
  avg_scan_duration_seconds: number | null;
  fix_rate_percent: number;
}

export interface SeverityTrendPoint {
  date: string;
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface RepoHealth {
  repository_id: string;
  repository_name: string;
  health_score: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  last_scanned_at: string | null;
}

export interface FixRatePoint {
  date: string;
  open: number;
  resolved: number;
  suppressed: number;
}

export function useOverviewStats() {
  return useQuery({
    queryKey: ["analytics", "overview"],
    queryFn: () =>
      api.get<{ success: boolean; data: OverviewStats }>("/analytics/overview/").then((r) => r.data.data),
    staleTime: 1000 * 60,
  });
}

export function useSeverityTrend(days = 30) {
  return useQuery({
    queryKey: ["analytics", "severity-trend", days],
    queryFn: () =>
      api.get<{ success: boolean; data: SeverityTrendPoint[] }>("/analytics/severity-trend/", { params: { days } })
        .then((r) => r.data.data),
    staleTime: 1000 * 60 * 5,
  });
}

export function useTopCategories(limit = 10) {
  return useQuery({
    queryKey: ["analytics", "top-categories", limit],
    queryFn: () =>
      api.get<{ success: boolean; data: CategoryCount[] }>("/analytics/top-vulnerability-categories/", { params: { limit } })
        .then((r) => r.data.data),
  });
}

export function useRepositoryHealth() {
  return useQuery({
    queryKey: ["analytics", "repo-health"],
    queryFn: () =>
      api.get<{ success: boolean; data: RepoHealth[] }>("/analytics/repository-health/").then((r) => r.data.data),
  });
}

export function useFixRate(days = 30) {
  return useQuery({
    queryKey: ["analytics", "fix-rate", days],
    queryFn: () =>
      api.get<{ success: boolean; data: FixRatePoint[] }>("/analytics/fix-rate/", { params: { days } })
        .then((r) => r.data.data),
  });
}
