const ATTACK_COLORS = {
  DoS: '#ef4444',
  Exploits: '#f97316',
  Reconnaissance: '#eab308',
  Generic: '#a855f7',
  Fuzzers: '#3b82f6',
  Analysis: '#06b6d4',
  Backdoor: '#ec4899',
  Shellcode: '#10b981',
  Worms: '#6366f1',
  Normal: '#22c55e',
}

export default function AttackBreakdown({ stats }) {
  const counts = stats?.attack_type_counts ?? {}
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1])

  if (sorted.length === 0) return null

  const max = sorted[0][1]

  return (
    <div className="breakdown-panel">
      <h2>Attack Breakdown</h2>
      <div className="breakdown-bars">
        {sorted.map(([type, count]) => (
          <div key={type} className="breakdown-row">
            <span className="breakdown-label">{type}</span>
            <div className="breakdown-track">
              <div
                className="breakdown-fill"
                style={{
                  width: `${(count / max) * 100}%`,
                  backgroundColor: ATTACK_COLORS[type] || '#64748b',
                }}
              />
            </div>
            <span className="breakdown-count">{count}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
