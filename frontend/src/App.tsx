import React, { useEffect, useMemo, useState } from 'react'
import { fetchRecentThreats, fetchSeverityDistribution, fetchStats, fetchThreatTimeline, fetchThreatsByPlatform } from './api'

type ThreatEvent = { type: string; data: any }

function KPI({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div style={{ padding: 16, border: '1px solid #eaeaea', borderRadius: 12, background: 'linear-gradient(180deg,#ffffff,#fafafa)', boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
      <div style={{ fontSize: 12, color: '#6b7280' }}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 800 }}>{value}</div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section style={{ marginTop: 24 }}>
      <h2 style={{ margin: '0 0 12px 0', fontSize: 18 }}>{title}</h2>
      {children}
    </section>
  )
}

function Badge({ text, color }: { text: string; color: string }) {
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 8px',
      borderRadius: 999,
      background: color,
      color: '#fff',
      fontSize: 12,
      fontWeight: 700
    }}>{text}</span>
  )
}

const severityColor = (sev?: string) => {
  switch ((sev||'').toLowerCase()) {
    case 'critical': return '#991b1b'
    case 'high': return '#b91c1c'
    case 'medium': return '#d97706'
    case 'low': return '#2563eb'
    default: return '#6b7280'
  }
}

const pill = (text: string) => (
  <span style={{ border: '1px solid #e5e7eb', background: '#f3f4f6', color: '#111827', borderRadius: 999, padding: '2px 8px', fontSize: 12 }}>{text}</span>
)

export default function App() {
  const [events, setEvents] = useState<ThreatEvent[]>([])
  const [kpis, setKpis] = useState<any>(null)
  const [recent, setRecent] = useState<any[]>([])
  const [byPlatform, setByPlatform] = useState<any[]>([])
  const [bySeverity, setBySeverity] = useState<any[]>([])
  const [timeline, setTimeline] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const wsUrl = useMemo(() => {
    const loc = window.location
    const protocol = loc.protocol === 'https:' ? 'wss' : 'ws'
    return `${protocol}://${loc.hostname}:8000/api/ws`
  }, [])

  useEffect(() => {
    (async () => {
      try {
        setLoading(true)
        const [s, r, p, sev, tl] = await Promise.all([
          fetchStats(),
          fetchRecentThreats(24, 20),
          fetchThreatsByPlatform(),
          fetchSeverityDistribution(),
          fetchThreatTimeline(7)
        ])
        setKpis(s)
        setRecent(r)
        setByPlatform(p)
        setBySeverity(sev)
        setTimeline(tl)
      } catch (e: any) {
        setError(e?.message || 'Failed to load data')
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  useEffect(() => {
    const ws = new WebSocket(wsUrl)
    ws.onmessage = (msg) => {
      try {
        const evt: ThreatEvent = JSON.parse(msg.data)
        setEvents((prev) => [evt, ...prev].slice(0, 50))
      } catch {
        setEvents((prev) => [{ type: 'raw', data: msg.data }, ...prev].slice(0, 50))
      }
    }
    ws.onopen = () => ws.send('hello')
    return () => ws.close()
  }, [wsUrl])

  if (loading) {
    return (
      <div style={{ fontFamily: 'system-ui, sans-serif', padding: 24 }}>
        <div style={{ height: 8, width: 200, background: '#eee', borderRadius: 8, marginBottom: 12 }}></div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} style={{ height: 72, background: '#f5f5f5', borderRadius: 12 }}></div>
          ))}
        </div>
        <div style={{ height: 16 }} />
        <div style={{ height: 300, background: '#f8f8f8', borderRadius: 12 }} />
      </div>
    )
  }
  if (error) {
    return <div style={{ fontFamily: 'system-ui, sans-serif', padding: 24, color: '#b00' }}>Error: {error}</div>
  }
  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', padding: 24, maxWidth: 1240, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 12, border: '1px solid #e5e7eb', borderRadius: 12, background: 'linear-gradient(180deg,#ffffff,#f9fafb)' }}>
        <h1 style={{ margin: 0, fontSize: 22 }}>VIP Threat & Misinformation Dashboard</h1>
        <div style={{ fontSize: 12, color: '#6b7280' }}>Last scan: {new Date(kpis?.last_scan || Date.now()).toLocaleString()}</div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginTop: 16 }}>
        <KPI label="Active VIPs" value={kpis?.total_vips ?? '—'} />
        <KPI label="Threats Today" value={kpis?.threats_today ?? '—'} />
        <KPI label="High Severity" value={kpis?.high_severity_threats ?? '—'} />
        <KPI label="Platforms" value={kpis?.platforms_monitored ?? '—'} />
      </div>

      <Section title="Recent Threats">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 10 }}>
          {recent.map((t) => (
            <div key={t.id} style={{ padding: 14, border: '1px solid #eaeaea', borderRadius: 12, background: '#fff', boxShadow: '0 1px 2px rgba(0,0,0,0.04)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <strong style={{ fontSize: 16 }}>{t.vip_name}</strong>
                  {pill(t.platform)}
                  <Badge text={t.severity} color={severityColor(t.severity)} />
                  <span style={{ fontSize: 12, color: '#6b7280' }}>{(t.confidence_score*100).toFixed(0)}%</span>
                </div>
                <span style={{ fontSize: 12, color: '#6b7280' }}>{new Date(t.created_at).toLocaleString()}</span>
              </div>
              <div style={{ fontSize: 12, color: '#374151', marginTop: 6 }}>{t.threat_type}</div>
              <div style={{ marginTop: 8, color: '#111827' }}>{(t.content || '').slice(0, 500)}</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
                {t?.evidence?.is_misinformation ? pill('misinformation') : null}
                {t?.evidence?.is_impersonation ? pill('impersonation') : null}
                {t?.evidence?.cluster_id ? pill(`cluster:${t.evidence.cluster_id}`) : null}
              </div>
              <div style={{ marginTop: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <a href={t.source_url} target="_blank" rel="noreferrer">View Source</a>
                {t?.evidence?.screenshot_url ? <a href={t.evidence.screenshot_url} target="_blank" rel="noreferrer" style={{ fontSize: 12 }}>Screenshot</a> : null}
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Analytics">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <div style={{ border: '1px solid #eaeaea', borderRadius: 12, padding: 12, background: '#fff' }}>
            <h3 style={{ marginTop: 0 }}>By Platform</h3>
            <ul>
              {byPlatform.map((p) => (
                <li key={p.platform}>{p.platform}: {p.count}</li>
              ))}
            </ul>
          </div>
          <div style={{ border: '1px solid #eaeaea', borderRadius: 12, padding: 12, background: '#fff' }}>
            <h3 style={{ marginTop: 0 }}>By Severity</h3>
            <ul>
              {bySeverity.map((s) => (
                <li key={s.severity}>{s.severity}: {s.count}</li>
              ))}
            </ul>
          </div>
          <div style={{ gridColumn: '1 / -1', border: '1px solid #eaeaea', borderRadius: 12, padding: 12, background: '#fff' }}>
            <h3 style={{ marginTop: 0 }}>Timeline (last 7 days)</h3>
            <ul style={{ display: 'flex', gap: 12, listStyle: 'none', padding: 0 }}>
              {timeline.map((d) => (
                <li key={d.date} style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 12, color: '#777' }}>{d.date}</div>
                  <div style={{ fontSize: 18, fontWeight: 700 }}>{d.count}</div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Section>

      <Section title="Live Feed">
        <ul>
          {events.map((e, i) => (
            <li key={i}><pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(e, null, 2)}</pre></li>
          ))}
        </ul>
      </Section>
    </div>
  )
}


