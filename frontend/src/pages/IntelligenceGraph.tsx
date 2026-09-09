import { useSearchParams } from 'react-router-dom'
import IntelligenceGraphView from '../components/IntelligenceGraph'

export default function IntelligenceGraph() {
  const [params] = useSearchParams()
  return <div className="space-y-6"><div><p className="text-xs uppercase tracking-[0.2em] text-blue-600 font-semibold">Operations intelligence</p><h1 className="text-3xl font-bold text-slate-900 mt-1">Intelligence Graph</h1><p className="text-slate-600 mt-2">Navigate the evidence network behind complaints, customers, orders, policies, and potential incidents.</p></div><IntelligenceGraphView entityType={params.get('entity') || 'complaint'} entityId={params.get('id') || undefined} /></div>
}
