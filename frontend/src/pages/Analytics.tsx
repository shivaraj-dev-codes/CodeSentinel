import { useState } from "react";
import { useOverviewStats, useSeverityTrend, useTopCategories, useRepositoryHealth, useFixRate } from "../api/analytics";
import { SeverityTrendChart } from "../components/analytics/SeverityTrendChart";
import { CategoryDonut } from "../components/analytics/CategoryDonut";
import { HealthScoreCard } from "../components/analytics/HealthScoreCard";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area, CartesianGrid } from "recharts";

const DAYS_OPTIONS = [7, 30, 90, 365];

export function Analytics() {
  const [days, setDays] = useState(30);
  const { data: stats } = useOverviewStats();
  const { data: categories } = useTopCategories(10);
  const { data: health } = useRepositoryHealth();
  const { data: fixRate } = useFixRate(days);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-text-primary">Analytics</h1>
          <p className="text-sm text-text-secondary mt-0.5">Security trends and health metrics</p>
        </div>
        <div className="flex items-center gap-1 bg-bg-elevated border border-border-default rounded-md p-0.5">
          {DAYS_OPTIONS.map((d) => (
            <button key={d} onClick={() => setDays(d)}
              className={`px-3 py-1 rounded text-sm transition-colors ${days === d ? "bg-accent-primary text-white" : "text-text-secondary hover:text-text-primary"}`}>
              {d === 365 ? "1y" : d === 90 ? "90d" : d === 30 ? "30d" : "7d"}
            </button>
          ))}
        </div>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        {[
          { label: "Open Findings", value: stats?.total_open_findings ?? "—" },
          { label: "Fix Rate", value: stats?.fix_rate_percent ? `${stats.fix_rate_percent}%` : "—" },
          { label: "Scans This Week", value: stats?.scans_this_week ?? "—" },
          { label: "Avg Scan Duration", value: stats?.avg_scan_duration_seconds ? `${Math.round(stats.avg_scan_duration_seconds)}s` : "—" },
        ].map(({ label, value }) => (
          <div key={label} className="bg-bg-surface border border-border-default rounded-lg p-4">
            <div className="text-xs text-text-muted mb-1">{label}</div>
            <div className="text-xl font-bold text-text-primary font-mono">{value}</div>
          </div>
        ))}
      </div>

      {/* Trend chart */}
      <div className="bg-bg-surface border border-border-default rounded-lg p-5">
        <h3 className="text-sm font-medium text-text-primary mb-4">Findings Over Time — {days}-day window</h3>
        <SeverityTrendChart days={days} />
      </div>

      {/* Categories + donut */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div className="bg-bg-surface border border-border-default rounded-lg p-5">
          <h3 className="text-sm font-medium text-text-primary mb-4">Top Vulnerability Categories</h3>
          {categories && categories.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={categories} layout="vertical" margin={{ left: 40, right: 20, top: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#30363d" horizontal={false} />
                <XAxis type="number" tick={{ fill: "#8b949e", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="category" tick={{ fill: "#8b949e", fontSize: 11 }} axisLine={false} tickLine={false} width={120} />
                <Tooltip contentStyle={{ background: "#161b22", border: "1px solid #30363d", borderRadius: "6px", fontSize: 12 }} />
                <Bar dataKey="count" fill="#7c5cfc" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-text-muted text-sm">No data yet</div>
          )}
        </div>

        <CategoryDonut />
      </div>

      {/* Repository health table */}
      {health && health.length > 0 && (
        <div className="bg-bg-surface border border-border-default rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-border-muted">
            <h3 className="text-sm font-medium text-text-primary">Repository Health</h3>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-muted">
                {["Repository", "Health Score", "Critical", "High", "Medium", "Low", "Last Scan"].map((h) => (
                  <th key={h} className="px-4 py-2.5 text-left text-xs text-text-muted font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {health.map((r) => {
                const color = r.health_score < 40 ? "#ff6e6e" : r.health_score < 70 ? "#e3b341" : "#3fb950";
                return (
                  <tr key={r.repository_id} className="border-b border-border-muted last:border-0 hover:bg-bg-elevated row-transition">
                    <td className="px-4 py-3 font-medium text-text-primary">{r.repository_name}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-bg-elevated rounded-full h-1.5">
                          <div className="h-full rounded-full" style={{ width: `${r.health_score}%`, backgroundColor: color }} />
                        </div>
                        <span className="font-mono text-xs" style={{ color }}>{r.health_score}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-severity-critical font-mono text-xs">{r.critical || "—"}</td>
                    <td className="px-4 py-3 text-severity-high font-mono text-xs">{r.high || "—"}</td>
                    <td className="px-4 py-3 text-severity-medium font-mono text-xs">{r.medium || "—"}</td>
                    <td className="px-4 py-3 text-severity-low font-mono text-xs">{r.low || "—"}</td>
                    <td className="px-4 py-3 text-text-muted text-xs">{r.last_scanned_at ? new Date(r.last_scanned_at).toLocaleDateString() : "Never"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
