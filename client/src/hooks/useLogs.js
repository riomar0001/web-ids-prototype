import { useState, useEffect, useCallback, useRef } from 'react'

const API_URL = import.meta.env.VITE_API_URL || '/api'

const DEFAULT_PARAMS = {
  page: 1,
  page_size: 20,
  sort: 'desc',
  classification: '',
  client_ip: '',
  search: '',
}

export function useLogs(pollInterval = 5000) {
  const [params, setParams] = useState(DEFAULT_PARAMS)
  const [logs, setLogs] = useState([])
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    page_size: 20,
    total_pages: 1,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Keep a ref so the interval always uses the latest params
  const paramsRef = useRef(params)
  paramsRef.current = params

  const fetchLogs = useCallback(async (overrideParams) => {
    const current = { ...paramsRef.current, ...overrideParams }
    try {
      const query = new URLSearchParams()
      Object.entries(current).forEach(([key, value]) => {
        if (value !== '' && value !== null && value !== undefined) {
          query.set(key, value)
        }
      })

      const res = await fetch(`${API_URL}/logs?${query}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()

      setLogs(data.entries ?? [])
      setPagination({
        total: data.total ?? 0,
        page: data.page ?? 1,
        page_size: data.page_size ?? 20,
        total_pages: data.total_pages ?? 1,
      })
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  // Change any subset of params and reset to page 1
  const applyFilters = useCallback((updates) => {
    setParams((prev) => {
      const next = { ...prev, ...updates, page: updates.page ?? 1 }
      paramsRef.current = next
      fetchLogs(next)
      return next
    })
  }, [fetchLogs])

  const goToPage = useCallback((page) => {
    applyFilters({ page })
  }, [applyFilters])

  // Initial fetch + polling — always refreshes the current page/filters
  useEffect(() => {
    fetchLogs()
    const id = setInterval(() => fetchLogs(), pollInterval)
    return () => clearInterval(id)
  }, [fetchLogs, pollInterval])

  return {
    logs,
    pagination,
    params,
    loading,
    error,
    applyFilters,
    goToPage,
    refresh: () => fetchLogs(),
  }
}
