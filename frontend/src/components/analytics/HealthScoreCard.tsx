interface Props {
  score: number;
  size?: number;
}

export function HealthScoreCard({ score, size = 80 }: Props) {
  const color = score < 40 ? "#ff6e6e" : score < 70 ? "#e3b341" : "#3fb950";
  const circumference = 2 * Math.PI * 30;
  const strokeDasharray = `${(score / 100) * circumference} ${circumference}`;

  return (
    <div className="flex flex-col items-center gap-1">
      <svg viewBox="0 0 100 100" style={{ width: size, height: size }}>
        <circle cx="50" cy="50" r="40" fill="none" stroke="#21262d" strokeWidth="8" />
        <circle cx="50" cy="50" r="40" fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={`${(score / 100) * 2 * Math.PI * 40} ${2 * Math.PI * 40}`}
          strokeLinecap="round"
          transform="rotate(-90 50 50)"
        />
        <text x="50" y="55" textAnchor="middle" fontSize="20" fontWeight="700" fill={color} fontFamily="JetBrains Mono, monospace">
          {score}
        </text>
      </svg>
      <span className="text-xs text-text-muted">Health</span>
    </div>
  );
}
