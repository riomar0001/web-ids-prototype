import { useState } from 'react'
import FeatureModal from './FeatureModal'

const SKELETON_ROWS = 8

function SkeletonRow() {
  return (
    <tr>
      <td><span className="skeleton skeleton-cell" /></td>
      <td><span className="skeleton skeleton-badge" /></td>
      <td><span className="skeleton skeleton-cell-sm" /></td>
      <td><span className="skeleton skeleton-cell-lg" /></td>
      <td><span className="skeleton skeleton-badge" /></td>
      <td><span className="skeleton skeleton-cell-sm" /></td>
      <td><span className="skeleton skeleton-btn" /></td>
    </tr>
  )
}

export default function LogTable({ logs, loading }) {
  const [selected, setSelected] = useState(null)

  return (
    <>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Method</th>
              <th>Client IP</th>
              <th>Endpoint</th>
              <th>Classification</th>
              <th>Features</th>
            </tr>
          </thead>
          <tbody>
            {loading && logs.length === 0
              ? Array.from({ length: SKELETON_ROWS }, (_, i) => <SkeletonRow key={i} />)
              : logs.map((entry, i) => (
                  <tr
                    key={i}
                    className={
                      entry.binary_classification === 'Attack' ? 'row-attack' : 'row-normal'
                    }
                  >
                    <td className="cell-mono">
                      {new Date(entry.timestamp).toLocaleString()}
                    </td>
                    <td>
                      {entry.method ? (
                        <span className={`badge badge-method badge-${(entry.method || 'get').toLowerCase()}`}>
                          {entry.method}
                        </span>
                      ) : '—'}
                    </td>
                    <td className="cell-mono">{entry.client_ip}</td>
                    <td className="cell-endpoint" title={entry.endpoint}>
                      {entry.endpoint}
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          entry.binary_classification === 'Attack' ? 'badge-attack' : 'badge-normal'
                        }`}
                      >
                        {entry.binary_classification}
                      </span>
                    </td>
                    <td>
                      <button
                        className="btn-features"
                        onClick={() => setSelected(entry)}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}

            {!loading && logs.length === 0 && (
              <tr>
                <td colSpan="7" className="empty-row">
                  No entries match the current filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {selected && (
        <FeatureModal entry={selected} onClose={() => setSelected(null)} />
      )}
    </>
  )
}
