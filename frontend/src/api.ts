export type MonitoringStats = {
  total_vips: number
  active_monitors: number
  threats_today: number
  high_severity_threats: number
  platforms_monitored: number
  last_scan?: string
}

export type Threat = {
  id: string
  vip_id: string
  vip_name: string
  platform: string
  threat_type: string
  severity: string
  confidence_score: number
  content: string
  source_url: string
  status: string
  created_at: string
}

const API_BASE = () => {
  const { protocol, hostname } = window.location
  const envHost = import.meta?.env?.VITE_API_HOST as string | undefined
  const envPort = (import.meta?.env?.VITE_API_PORT as string | undefined) ?? '8000'
  const host = envHost && envHost.length > 0 ? envHost : hostname
  return `${protocol}//${host}:${envPort}`
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE()}${path}`)
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`)
  return res.json()
}

export const fetchStats = () => get<MonitoringStats>(`/api/stats`)

export const fetchRecentThreats = (hours = 24, limit = 25) =>
  get<Threat[]>(`/api/threats/recent?hours=${hours}&limit=${limit}`)

export const fetchThreatsByPlatform = () =>
  get<{ platform: string; count: number }[]>(`/api/analytics/threats-by-platform`)

export const fetchSeverityDistribution = () =>
  get<{ severity: string; count: number }[]>(`/api/analytics/severity-distribution`)

export const fetchThreatTimeline = (days = 7) =>
  get<{ date: string; count: number }[]>(`/api/analytics/threat-timeline?days=${days}`)


