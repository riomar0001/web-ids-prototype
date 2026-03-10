import { useState, useEffect, useCallback } from 'react'

const API_URL = import.meta.env.VITE_API_URL || '/api'

const EMPTY = {
  total_requests: 0,
  total_attacks: 0,
  total_normal: 0,
  unique_ips: 0,
  top_attack_type: null,
  attack_type_counts: {},
}

export function useStats(pollInterval = 5000) {
  const [stats, setStats] = useState(EMPTY)
  const [loaded, setLoaded] = useState(false)

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/logs/stats`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setStats({ ...EMPTY, ...data })
    } catch {
      // stats endpoint unavailable — keep last known values, still mark loaded
    } finally {
      setLoaded(true)
    }
  }, [])

  useEffect(() => {
    fetchStats()
    const id = setInterval(fetchStats, pollInterval)
    return () => clearInterval(id)
  }, [fetchStats, pollInterval])

  return { stats, loaded }
}
