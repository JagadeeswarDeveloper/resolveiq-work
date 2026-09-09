import { type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { customerAPI, graphAPI, intelligenceAPI, type Complaint, type CriticEvaluation, type DecisionTraceEvent } from '../lib/api'

export function Customer360Panel({ customerId }: { customerId: string }) {
  const customer = useQuery({ queryKey: ['customer', customerId], queryFn: () => customerAPI.get(customerId).then(response => response.data) })
  const risk = useQuery({ queryKey: ['customer-risk', customerId], queryFn: () => customerAPI.risk(customerId).then(response => response.data.data.risk) })
  if (customer.isLoading || risk.isLoading) return <Panel title="Customer 360"><p className="text-sm text-slate-500">Loading customer intelligence...</p></Panel>
  if (!customer.data || !risk.data) return <Panel title="Customer 360"><p className="text-sm text-slate-500">Customer intelligence unavailable.</p></Panel>
  return <Panel title="Customer 360" eyebrow="Explainable customer risk"><div className="flex items-end justify-between gap-3"><div><p className="text-3xl font-bold">{risk.data.score}/100</p><p className={`text-sm font-semibold ${risk.data.risk_level === 'HIGH' ? 'text-red-600' : risk.data.risk_level === 'MEDIUM' ? 'text-amber-600' : 'text-emerald-600'}`}>{risk.data.risk_level} RISK</p></div><Link className="text-sm text-blue-600 hover:underline" to={`/customers/${customer.data.id}`}>View Customer 360</Link></div><p className="mt-3 font-medium">{customer.data.name} · {customer.data.tier || 'Tier unavailable'}</p><div className="grid grid-cols-3 gap-2 mt-4 text-center text-sm"><Metric label="Orders" value={risk.data.order_count ?? customer.data.complaints_count} /><Metric label="Open" value={risk.data.open_complaints ?? '—'} /><Metric label="Repeat" value={risk.data.repeat_complaint_count ?? '—'} /></div><div className="mt-4"><p className="text-xs uppercase tracking-wider text-slate-500">Reasons for risk</p>{risk.data.reasons.length ? <ul className="mt-2 list-disc list-inside text-sm text-slate-700">{risk.data.reasons.map(reason => <li key={reason}>{reason}</li>)}</ul> : <p className="text-sm text-slate-500 mt-2">No elevated signals detected.</p>}</div></Panel>
}

export function DecisionTracePanel({ complaint }: { complaint: Complaint }) {
  const trace = useQuery({ queryKey: ['decision-trace', complaint.id], queryFn: () => intelligenceAPI.decisionTrace(complaint.id).then(response => response.data.events), initialData: complaint.decision_trace || [] })
  return <Panel title="Decision Trace" eyebrow="Structured evidence trail"><div className="space-y-3">{trace.data?.length ? trace.data.map((event: DecisionTraceEvent, index: number) => <div className="flex gap-3" key={`${event.step}-${index}`}><div className="flex flex-col items-center"><span className="w-3 h-3 rounded-full bg-blue-600 mt-1" />{index < trace.data.length - 1 && <span className="w-px bg-blue-200 flex-1" />}</div><div className="pb-3"><p className="font-medium text-sm">{event.step}</p><p className="text-sm text-slate-600">{event.result}</p><p className="text-xs text-slate-400 mt-1">{event.source}{event.confidence ? ` · ${(event.confidence * 100).toFixed(0)}% confidence` : ''}</p></div></div>) : <p className="text-sm text-slate-500">Trace events appear as the workflow advances.</p>}</div></Panel>
}

export function CriticPanel({ complaintId }: { complaintId: string }) {
  const critic = useQuery({ queryKey: ['critic', complaintId], queryFn: () => intelligenceAPI.critic(complaintId).then(response => response.data) })
  if (critic.isLoading) return <Panel title="Resolution Review"><p className="text-sm text-slate-500">Evaluating recommendation...</p></Panel>
  if (critic.isError || !critic.data) return <Panel title="Resolution Review"><p className="text-sm text-slate-500">Critic evaluation will be available after a recommendation is generated.</p></Panel>
  const checks: [keyof CriticEvaluation, string][] = [['policy_compliance', 'Policy Compliance'], ['evidence_support', 'Evidence Support'], ['customer_context', 'Customer Context'], ['action_validity', 'Action Validity']]
  return <Panel title="Resolution Review" eyebrow="Critic Agent"><div className="grid grid-cols-2 gap-2">{checks.map(([key, label]) => <div key={key} className="border border-slate-200 rounded p-3"><p className="text-xs text-slate-500">{label}</p><p className={`font-semibold mt-1 ${critic.data[key] === 'PASS' ? 'text-emerald-600' : 'text-red-600'}`}>{critic.data[key]}</p></div>)}</div><div className="mt-4 flex justify-between items-center"><span className="text-sm">Hallucination risk: <strong>{critic.data.hallucination_risk}</strong></span><span className={`px-3 py-1 rounded-full text-xs font-semibold ${critic.data.overall_recommendation === 'PASS' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>{critic.data.overall_recommendation === 'PASS' ? 'APPROVED FOR SUPERVISOR' : 'REVISION REQUIRED'}</span></div></Panel>
}

export function GraphContextPanel({ complaint }: { complaint: Complaint }) {
  const graph = useQuery({ queryKey: ['complaint-graph', complaint.id], queryFn: () => graphAPI.overview('complaint', complaint.id, 30).then(response => response.data) })
  return <Panel title="Graph Context" eyebrow="Connected enterprise evidence"><div className="flex flex-wrap gap-2">{graph.data?.nodes.filter(node => node.type !== 'complaint').slice(0, 10).map(node => <span key={`${node.type}-${node.id}`} className="px-3 py-1 rounded-full bg-slate-100 text-sm text-slate-700">{node.type}: {node.label}</span>)}</div><Link to={`/intelligence-graph?entity=complaint&id=${complaint.id}`} className="inline-block mt-4 text-sm text-blue-600 hover:underline">Open in Intelligence Graph</Link></Panel>
}

function Panel({ title, eyebrow, children }: { title: string; eyebrow?: string; children: ReactNode }) { return <section className="bg-white p-6 rounded-lg shadow"><div className="flex items-baseline justify-between gap-3 mb-4"><div><p className="text-xs uppercase tracking-wider text-slate-500">{eyebrow}</p><h2 className="text-lg font-semibold">{title}</h2></div></div>{children}</section> }
function Metric({ label, value }: { label: string; value: string | number }) { return <div className="bg-slate-50 rounded p-2"><p className="font-semibold">{value}</p><p className="text-xs text-slate-500">{label}</p></div> }
