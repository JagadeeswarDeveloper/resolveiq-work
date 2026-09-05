import { useQuery } from '@tanstack/react-query'
import { dashboardAPI, incidentAPI } from '../lib/api'
import StatCard from '../components/StatCard'
import ComplaintChart from '../components/ComplaintChart'
import QuickActions from '../components/QuickActions'
import { AlertCircle, CheckCircle2, Clock, Siren, ShieldAlert, UserCheck } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => dashboardAPI.summary().then(r => r.data),
    refetchInterval: 10000,
  })

  const { data: trends } = useQuery({
    queryKey: ['dashboard-trends'],
    queryFn: () => dashboardAPI.trends(7).then(r => r.data),
  })

  const { data: incidents } = useQuery({
    queryKey: ['incidents'],
    queryFn: () => incidentAPI.list().then(r => r.data),
    refetchInterval: 10000,
  })

  const demoMode = import.meta.env.VITE_DEMO_MODE === 'true'

  if (summaryLoading) {
    return <div className="text-center py-12">Loading dashboard...</div>
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3"><h1 className="text-4xl font-bold text-gray-900">Dashboard</h1>{demoMode && <span className="px-2 py-1 text-xs font-bold tracking-wide rounded bg-amber-100 text-amber-800">DEMO MODE</span>}</div>
        <p className="text-gray-600 mt-2">Multi-Agent Customer Complaint Intelligence Platform</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Complaints"
          value={summary?.total_complaints || 0}
          icon={<AlertCircle className="w-6 h-6" />}
          color="bg-red-50"
        />
        <StatCard
          title="Open Complaints"
          value={summary?.open_complaints || 0}
          icon={<Clock className="w-6 h-6" />}
          color="bg-yellow-50"
        />
        <StatCard
          title="High Priority"
          value={summary?.high_priority_complaints || 0}
          icon={<ShieldAlert className="w-6 h-6" />}
          color="bg-orange-50"
        />
        <StatCard
          title="SLA Breaches"
          value={summary?.sla_breaches || 0}
          icon={<Clock className="w-6 h-6" />}
          color="bg-yellow-50"
        />
        <StatCard
          title="Auto-Resolved"
          value={`${(summary?.auto_resolution_rate || 0) * 100 || 0}%`}
          icon={<CheckCircle2 className="w-6 h-6" />}
          color="bg-green-50"
        />
        <StatCard
          title="Human Approval"
          value={`${(summary?.human_approval_rate || 0) * 100 || 0}%`}
          icon={<UserCheck className="w-6 h-6" />}
          color="bg-blue-50"
        />
        <StatCard
          title="Active Incidents"
          value={summary?.active_incidents || 0}
          icon={<AlertCircle className="w-6 h-6" />}
          color="bg-purple-50"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Complaint Trends (7 days)</h2>
          <ComplaintChart data={trends || []} />
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Avg Resolution Time</h2>
          <p className="text-3xl font-bold text-blue-600">
            {summary?.avg_resolution_time_hours || 0} hrs
          </p>
          <p className="text-gray-600 mt-2">SLA Breach Rate: {((summary?.sla_breach_rate || 0) * 100).toFixed(1)}%</p>
        </div>
      </div>

      <section className="bg-slate-950 text-white rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2"><Siren className="w-5 h-5 text-red-400" /><h2 className="text-lg font-semibold">Incident Intelligence</h2></div>
          <Link className="text-sm text-blue-300 hover:text-white" to="/incidents">View all</Link>
        </div>
        {incidents?.length ? incidents.slice(0, 3).map(incident => (
          <Link to={`/incidents/${incident.id}`} key={incident.id} className="block border-t border-slate-700 py-4 hover:bg-slate-900">
            <div className="flex justify-between gap-4"><span className="font-medium">Potential Incident: {incident.title}</span><span className="text-red-300 text-sm">{incident.status}</span></div>
            <p className="text-slate-300 text-sm mt-1">{incident.complaint_count} linked complaints · {incident.volume_change_percent?.toFixed(0) || 0}% volume change · {(incident.confidence * 100).toFixed(0)}% confidence</p>
          </Link>
        )) : <p className="text-slate-300">No potential incidents detected.</p>}
      </section>

      {/* Quick Actions */}
      <QuickActions />
    </div>
  )
}
