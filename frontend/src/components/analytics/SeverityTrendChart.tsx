import { useSeverityTrend } from "../../api/analytics";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { format, parseISO } from "date-fns";

interface Props { days?: number; }

export function SeverityTrendChart({ days = 30 }: Props) {
  const { data, isLoading } = useSeverityTrend(days);

  if (isLoading) {
    return <div className="h-48 bg-bg-elevated rounded animate-pulse" />;
  }

  const formatted = (data ?? []).map((d) => ({
    ...d,
    date: format(parseISO(d.date), "MMM d"),
  }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={formatted} margin={{ top: 4, right: 16, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
        <XAxis dataKey="date" tick={{ fill: "#8b949e", fontSize: 11 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
        <YAxis tick={{ fill: "#8b949e", fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip
          contentStyle={{ background: "#161b22", border: "1px solid #30363d", borderRadius: "6px", fontSize: 12 }}
          labelStyle={{ color: "#e6edf3" }}
        />
        <Legend wrapperStyle={{ fontSize: 12, color: "#8b949e" }} />
        <Line type="monotone" dataKey="critical" stroke="#ff6e6e" dot={false} strokeWidth={2} />
        <Line type="monotone" dataKey="high" stroke="#ff9500" dot={false} strokeWidth={2} />
        <Line type="monotone" dataKey="medium" stroke="#e3b341" dot={false} strokeWidth={2} />
        <Line type="monotone" dataKey="low" stroke="#3fb950" dot={false} strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );
}
