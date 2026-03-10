import { useLogs } from './hooks/useLogs'
import { useStats } from './hooks/useStats'
import StatsBar from './components/StatsBar'
import AttackBreakdown from './components/AttackBreakdown'
import Filters from './components/Filters'
import LogTable from './components/LogTable'
import Pagination from './components/Pagination'
import './App.css'

export default function App() {
  const { logs, pagination, params, loading, error, applyFilters, goToPage, refresh } =
    useLogs(5000)
  const { stats, loaded: statsLoaded } = useStats(5000)

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <h1>IDS Dashboard</h1>
          <span className="header-subtitle">Intrusion Detection System Monitor</span>
        </div>
        <div className="header-right">
          {error && <span className="error-badge" title={error}>Connection error</span>}
          {loading && <span className="loading-badge">Updating…</span>}
          <button className="btn-refresh" onClick={refresh}>Refresh</button>
        </div>
      </header>

      <StatsBar stats={stats} loaded={statsLoaded} />
      <AttackBreakdown stats={stats} />

      <div className="table-section">
        <div className="table-header">
          <h2>
            Detection Log
            <span className="table-count">
              {loading ? '—' : pagination.total.toLocaleString()} entries
            </span>
          </h2>
        </div>

        <Filters params={params} onApply={applyFilters} />
        <LogTable logs={logs} loading={loading} />
        <Pagination pagination={pagination} onPageChange={goToPage} />
      </div>
    </div>
  )
}
