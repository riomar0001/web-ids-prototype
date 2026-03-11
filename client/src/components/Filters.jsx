import { useState } from 'react'


export default function Filters({ params, onApply }) {
  const [search, setSearch] = useState(params.search)
  const [clientIp, setClientIp] = useState(params.client_ip)

  function handleClassification(value) {
    onApply({ classification: value })
  }

  function handleSearch(e) {
    setSearch(e.target.value)
  }

  function handleIp(e) {
    setClientIp(e.target.value)
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') {
      onApply({ search, client_ip: clientIp })
    }
  }

  function handleClear() {
    setSearch('')
    setClientIp('')
    onApply({ classification: '', search: '', client_ip: '' })
  }

  const hasFilters =
    params.classification || params.search || params.client_ip

  return (
    <div className="filters-bar">
      {/* Classification toggle */}
      <div className="filter-group">
        {[
          { label: 'All', value: '' },
          { label: 'Normal', value: 'Normal' },
          { label: 'Attack', value: 'Attack' },
        ].map(({ label, value }) => (
          <button
            key={label}
            className={`filter-btn ${params.classification === value ? 'active' : ''}`}
            onClick={() => handleClassification(value)}
          >
            {label}
          </button>
        ))}
      </div>

      {/* IP filter */}
      <input
        className="filter-input"
        type="text"
        placeholder="Client IP..."
        value={clientIp}
        onChange={handleIp}
        onKeyDown={handleKeyDown}
      />

      {/* Endpoint / keyword search */}
      <input
        className="filter-input filter-input-wide"
        type="text"
        placeholder="Search endpoint or IP..."
        value={search}
        onChange={handleSearch}
        onKeyDown={handleKeyDown}
      />

      <button
        className="filter-btn-apply"
        onClick={() => onApply({ search, client_ip: clientIp })}
      >
        Apply
      </button>

      {hasFilters && (
        <button className="filter-btn-clear" onClick={handleClear}>
          Clear
        </button>
      )}
    </div>
  )
}
