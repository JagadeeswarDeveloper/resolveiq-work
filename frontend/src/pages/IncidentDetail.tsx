import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { incidentAPI } from '../lib/api'
import { AlertTriangle, Activity, Users, ShieldAlert } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import IncidentImpactPanel from '../components/IncidentImpactPanel'

export default function IncidentDetail() {
  const { id } = useParams<{ id: string }>()
  const incident = useQuery({ queryKey: ['incident', id], queryFn: () => incidentAPI.get(id!).then(r => r.data) })
  const complaints = useQuery({ queryKey: ['incident-complaints', id], queryFn: () => incidentAPI.complaints(id!).then(r => r.data.data?.complaints ?? []) })
  const evidence = useQuery({ queryKey: ['incident-evidence', id], queryFn: () => incidentAPI.evidence(id!).then(r => r.data) })
  if (incident.isLoading) return <p>Loading incident...</p>
  if (!incident.data) return <p>Incident not found.</p>
  const item = incident.data
  const metrics: { icon: LucideIcon; label: string; value: string | number }[] = [
    { icon: Users, label: 'Linked complaints', value: item.complaint_count },
    { icon: ShieldAlert, label: 'SLA breaches', value: item.sla_breach_count || 0 },
    { icon: AlertTriangle, label: 'High priority', value: item.high_priority_count || 0 },
    { icon: Activity, label: 'Volume change', value: `${(item.volume_change_percent || 0).toFixed(0)}%` },
  ]
  return <div className="space-y-6"><div><h1 className="text-3xl font-bold">{item.title}</h1><p className="text-gray-600">Potential incident · {item.status} · {(item.confidence * 100).toFixed(0)}% confidence</p></div><div className="grid grid-cols-2 md:grid-cols-4 gap-4">{metrics.map(({ icon: Icon, label, value }) => <div className="bg-white p-4 rounded-lg shadow" key={label}><Icon className="w-5 h-5 text-red-600 mb-2" /><p className="text-sm text-gray-500">{label}</p><p className="text-2xl font-bold">{value}</p></div>)}</div><div className="bg-white p-6 rounded-lg shadow space-y-3"><h2 className="font-semibold">Potential root cause</h2><p>{item.potential_root_cause || item.suspected_root_cause || 'Under investigation'}</p><p className="text-sm text-gray-600">{item.evidence_summary}</p><h2 className="font-semibold pt-3">Recommended actions</h2><ul className="list-disc list-inside text-gray-700"><li>Investigate the affected operation</li><li>Review partner or warehouse status</li><li>Monitor complaint volume and affected customers</li></ul></div><IncidentImpactPanel incidentId={item.id} /><div className="bg-white p-6 rounded-lg shadow"><h2 className="font-semibold mb-3">Evidence signals</h2>{evidence.data?.map((record: any) => <div key={record.id} className="text-sm text-gray-700">{record.signals_used?.join(' · ')} · {record.complaint_ids?.length || 0} complaints</div>)}</div><div className="bg-white p-6 rounded-lg shadow"><h2 className="font-semibold mb-3">Related complaints</h2>{complaints.data?.map(complaint => <Link className="block text-blue-700 py-1" to={`/complaints/${complaint.id}`} key={complaint.id}>{complaint.raw_text}</Link>)}</div></div>
}