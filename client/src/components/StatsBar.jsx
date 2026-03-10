export default function StatsBar({ stats, loaded }) {
  const {
    total_requests,
    total_attacks,
    total_normal,
    unique_ips,
    top_attack_type,
    attack_type_counts,
  } = stats ?? {}

  const topCount = top_attack_type ? (attack_type_counts?.[top_attack_type] ?? 0) : null

  const cards = [
    { value: total_requests ?? 0, label: 'Total Requests' },
    { value: total_normal ?? 0,   label: 'Normal',   cls: 'stat-normal' },
    { value: total_attacks ?? 0,  label: 'Attacks',  cls: 'stat-attack' },
    { value: unique_ips ?? 0,     label: 'Unique IPs' },
    {
      value: top_attack_type ?? '—',
      label: `Top Attack${topCount ? ` (${topCount})` : ''}`,
    },
  ]

  return (
    <div className="stats-bar">
      {cards.map(({ value, label, cls }) => (
        <div key={label} className={`stat-card ${cls ?? ''}`}>
          {loaded ? (
            <span className="stat-value">
              {typeof value === 'number' ? value.toLocaleString() : value}
            </span>
          ) : (
            <span className="skeleton skeleton-value" />
          )}
          <span className="stat-label">{label}</span>
        </div>
      ))}
    </div>
  )
}
