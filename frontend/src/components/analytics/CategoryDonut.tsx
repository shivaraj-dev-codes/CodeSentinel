import { useTopCategories } from "../../api/analytics";
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";

const COLORS = ["#ff6e6e", "#ff9500", "#e3b341", "#3fb950", "#58a6ff", "#7c5cfc", "#c9d1d9", "#484f58", "#f0883e", "#a5d6ff"];

export function CategoryDonut() {
  const { data, isLoading } = useTopCategories(8);

  if (isLoading) {
    return <div className="bg-bg-surface border border-border-default rounded-lg p-5 h-72 animate-pulse" />;
  }

  const total = (data ?? []).reduce((s, d) => s + d.count, 0);

  return (
    <div className="bg-bg-surface border border-border-default rounded-lg p-5">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-text-primary">Severity Distribution</span>
        <span className="text-xs text-text-muted">{total} open findings</span>
      </div>
      {total === 0 ? (
        <div className="h-48 flex items-center justify-center text-text-muted text-sm">No findings yet</div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie data={data} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={2} dataKey="count">
              {(data ?? []).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie>
            <Tooltip contentStyle={{ background: "#161b22", border: "1px solid #30363d", borderRadius: "6px", fontSize: 12 }} />
            <Legend wrapperStyle={{ fontSize: 11, color: "#8b949e" }} />
          </PieChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
