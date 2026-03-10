export default function FeatureModal({ entry, onClose }) {
  if (!entry) return null

  const features = entry.features || {}
  const explanation = entry.explanation || []
  const maxAbs = explanation.reduce((m, e) => Math.max(m, Math.abs(e.shap_value)), 0) || 1

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Feature Details</h2>
          <button className="modal-close" onClick={onClose}>
            &times;
          </button>
        </div>

        <div className="modal-meta">
          <p>
            <strong>Endpoint:</strong>{' '}
            {entry.method && (
              <span className={`badge badge-method badge-${entry.method.toLowerCase()}`} style={{ marginRight: '6px' }}>
                {entry.method}
              </span>
            )}
            {entry.endpoint}
          </p>
          <p>
            <strong>Client IP:</strong> {entry.client_ip}
          </p>
          <p>
            <strong>Time:</strong> {new Date(entry.timestamp).toLocaleString()}
          </p>
          <p>
            <strong>Classification:</strong>{' '}
            <span
              className={`badge ${
                entry.binary_classification === 'Attack' ? 'badge-attack' : 'badge-normal'
              }`}
            >
              {entry.binary_classification}
            </span>
            {entry.attack_type && ` — ${entry.attack_type}`}
          </p>
        </div>

        {explanation.length === 0 && (
          <div className="xai-section xai-empty">
            <div className="xai-header">
              <h3 className="xai-title">Top Contributing Features</h3>
              <span className="xai-tag">SHAP</span>
            </div>
            <p className="xai-subtitle">No explanation available — this entry was recorded before XAI was enabled.</p>
          </div>
        )}

        {explanation.length > 0 && (
          <div className="xai-section">
            <div className="xai-header">
              <h3 className="xai-title">Top Contributing Features</h3>
              <span className="xai-tag">SHAP</span>
            </div>
            <p className="xai-subtitle">
              <span className="xai-legend xai-legend-positive">■</span> pushes toward Attack
              &nbsp;·&nbsp;
              <span className="xai-legend xai-legend-negative">■</span> pushes toward Normal
            </p>
            <div className="xai-bars">
              {explanation.map(({ feature, value, shap_value }) => {
                const isPositive = shap_value >= 0
                const pct = Math.round((Math.abs(shap_value) / maxAbs) * 100)
                return (
                  <div key={feature} className="xai-row">
                    <div className="xai-feature-name" title={feature}>{feature}</div>
                    <div className="xai-bar-track">
                      <div
                        className={`xai-bar-fill ${isPositive ? 'xai-positive' : 'xai-negative'}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <div className={`xai-shap-value ${isPositive ? 'xai-text-positive' : 'xai-text-negative'}`}>
                      {isPositive ? '+' : ''}{shap_value.toFixed(4)}
                    </div>
                    <div className="xai-raw-value">
                      {typeof value === 'number' ? value.toLocaleString() : value}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        <h3 className="all-features-title">All Features</h3>
        <div className="feature-grid">
          {Object.entries(features).map(([name, value]) => (
            <div key={name} className="feature-item">
              <span className="feature-name">{name}</span>
              <span className="feature-value">
                {typeof value === 'number' ? value.toLocaleString() : value}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
