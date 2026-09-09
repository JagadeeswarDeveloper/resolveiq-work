import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Minus, Plus, RefreshCw, Search, Sparkles } from 'lucide-react'
import { complaintAPI, graphAPI, type GraphNode } from '../lib/api'

type IntelligenceGraphProps = { compact?: boolean; entityType?: string; entityId?: string }

type PositionedNode = GraphNode & { x: number; y: number; level: 'root' | 'primary' | 'secondary'; hiddenCount?: number }

const nodeColors: Record<string, string> = {
  customer: '#0f766e', complaint: '#2563eb', order: '#7c3aed', incident: '#dc2626', policy: '#b45309', resolution: '#059669', product: '#0891b2', region: '#64748b', warehouse: '#ea580c', carrier: '#4f46e5', payment: '#be185d', default: '#475569',
}

const preferredTypes = ['customer', 'order', 'policy', 'warehouse', 'incident', 'product', 'carrier', 'region', 'payment', 'resolution']
export default function IntelligenceGraph({ compact = false, entityType, entityId }: IntelligenceGraphProps) {
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('all')
  const [selected, setSelected] = useState<string | null>(entityId ? `${entityType || 'complaint'}:${entityId}` : null)
  const [expandedTypes, setExpandedTypes] = useState<string[]>([])
  const [zoom, setZoom] = useState(1)
  const [explanationOpen, setExplanationOpen] = useState(false)

  const complaints = useQuery({ queryKey: ['graph-root-complaints'], queryFn: () => complaintAPI.list(0, 10).then(response => response.data), enabled: !entityId })
  const rootId = entityId || complaints.data?.[0]?.id
  const selectedParts = selected?.split(':') || []
  const rootType = selectedParts[0] || entityType || 'complaint'
  const selectedRootId = selectedParts[1] || rootId
  const graph = useQuery({ queryKey: ['intelligence-graph', rootType, selectedRootId], queryFn: () => graphAPI.overview(rootType, selectedRootId, 200).then(response => response.data), enabled: Boolean(selectedRootId) })

  const nodes = graph.data?.nodes || []
  const edges = graph.data?.edges || []
  const rootNodeId = selected || `${rootType}:${selectedRootId}`
  const rootNode = nodes.find(node => `${node.type}:${node.id}` === rootNodeId) || nodes.find(node => node.type === rootType && node.id === selectedRootId)
  const connectedEdges = edges.filter(edge => edge.source === rootNode?.id || edge.target === rootNode?.id)
  const connectedIds = new Set(connectedEdges.flatMap(edge => [edge.source, edge.target]))
  const directNodes = nodes.filter(node => node.id !== rootNode?.id && connectedIds.has(node.id))
  const availableTypes = Array.from(new Set(nodes.map(node => node.type))).filter(type => preferredTypes.includes(type) || type === rootType)
  const searchResults = nodes.filter(node => search && `${node.label} ${node.type}`.toLowerCase().includes(search.toLowerCase())).slice(0, 8)

  const positionedNodes = useMemo(() => {
    if (!rootNode) return []
    const grouped = new Map<string, GraphNode[]>()
    directNodes.filter(node => typeFilter === 'all' || node.type === typeFilter).forEach(node => {
      const group = grouped.get(node.type) || []
      group.push(node)
      grouped.set(node.type, group)
    })
    const visible: PositionedNode[] = [{ ...rootNode, x: 470, y: 270, level: 'root' }]
    const groups = Array.from(grouped.entries()).sort((a, b) => preferredTypes.indexOf(a[0]) - preferredTypes.indexOf(b[0]))
    groups.forEach(([type, group], groupIndex) => {
      const expanded = expandedTypes.includes(type)
      const limit = expanded ? Math.min(group.length, 12) : Math.min(group.length, 3)
      const shown = group.slice(0, limit)
      const angleStart = -Math.PI * 0.85 + groupIndex * 0.14
      shown.forEach((node, index) => {
        const angle = angleStart + (index / Math.max(1, shown.length - 1)) * Math.PI * 0.7
        visible.push({ ...node, x: 470 + Math.cos(angle) * 310, y: 270 + Math.sin(angle) * 205, level: 'primary' })
      })
      if (group.length > limit) visible.push({ type, id: `aggregate-${type}`, label: `${group.length} related ${type}${group.length === 1 ? '' : 's'}`, status: 'aggregate', metadata: {}, x: 470 + Math.cos(angleStart + 0.35) * 270, y: 270 + Math.sin(angleStart + 0.35) * 180, level: 'secondary', hiddenCount: group.length - limit })
    })
    return visible
  }, [rootNode, directNodes, expandedTypes, typeFilter])

  const positionMap = new Map(positionedNodes.filter(node => !node.id.startsWith('aggregate-')).map(node => [node.id, node]))
  const visibleEdges = edges.filter(edge => positionMap.has(edge.source) && positionMap.has(edge.target))
  const selectedNode = rootNode
  const selectedConnections = connectedEdges.length
  const relatedComplaintCount = nodes.filter(node => node.type === 'complaint' && node.id !== rootNode?.id).length
  const explainableSignals = [
    rootType === 'complaint' ? 'Customer and complaint context connected' : `${rootType} relationships inspected`,
    nodes.some(node => node.type === 'order') ? 'Order context available' : 'No order relationship in current evidence',
    nodes.some(node => node.type === 'incident') ? 'Potential incident relationship found' : 'No potential incident linked',
    nodes.some(node => node.type === 'policy') ? 'Relevant policy evidence connected' : 'No policy relationship found',
  ]

  const selectNode = (node: GraphNode) => {
    if (node.id.startsWith('aggregate-')) {
      setExpandedTypes(current => current.includes(node.type) ? current.filter(type => type !== node.type) : [...current, node.type])
      return
    }
    setSelected(`${node.type}:${node.id}`)
    setExpandedTypes([])
    setExplanationOpen(false)
  }

  return <div className={compact ? 'bg-slate-950 rounded-lg p-4 text-white' : 'space-y-5'}>
    {!compact && <div className="bg-slate-950 text-white rounded-lg p-6"><div className="flex flex-wrap justify-between gap-4"><div><p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Why this matters</p><h2 className="text-2xl font-semibold mt-2">Contextual enterprise evidence</h2><p className="text-slate-300 mt-2 max-w-2xl">Start from one meaningful entity. Expand only the relationships that help explain the operational pattern.</p></div><button onClick={() => setExplanationOpen(value => !value)} className="h-fit flex items-center gap-2 px-4 py-2 rounded bg-cyan-400 text-slate-950 font-semibold"><Sparkles className="w-4 h-4" /> Explain this network</button></div>{explanationOpen && <div className="mt-5 border-t border-slate-700 pt-4"><p className="font-semibold">Network insight</p><p className="text-slate-300 mt-2">This {rootType} is connected to {selectedConnections} direct evidence relationships{relatedComplaintCount ? ` and ${relatedComplaintCount} related complaints are available for expansion` : ''}. The network suggests a potential operational pattern based on linked entities, not proven causality.</p><div className="flex flex-wrap gap-2 mt-3">{explainableSignals.map(signal => <span key={signal} className="bg-white/10 px-3 py-2 rounded text-sm">{signal}</span>)}</div><p className="text-sm text-cyan-300 mt-3">Confidence is derived from the available relationship evidence.</p></div>}</div>}

    <div className={compact ? 'space-y-3' : 'bg-white rounded-lg shadow p-4'}>
      <div className="flex flex-wrap gap-2 items-center"><label className="relative flex items-center gap-2 flex-1 min-w-[240px] border border-slate-300 rounded px-3 py-2"><Search className="w-4 h-4 text-slate-400" /><input value={search} onChange={event => setSearch(event.target.value)} placeholder="Search customers, complaints, orders, policies, incidents..." className={compact ? 'bg-transparent text-white outline-none w-full' : 'outline-none w-full'} />{searchResults.length > 0 && <div className="absolute top-full left-0 right-0 z-20 mt-1 bg-white border rounded shadow text-slate-800">{searchResults.map(result => <button key={`${result.type}-${result.id}`} onClick={() => { selectNode(result); setSearch('') }} className="block w-full text-left px-3 py-2 hover:bg-slate-100 text-sm"><span className="font-medium">{result.label}</span><span className="text-slate-500 ml-2">{result.type}</span></button>)}</div>}</label><select value={typeFilter} onChange={event => setTypeFilter(event.target.value)} className="border border-slate-300 rounded px-3 py-2 text-sm text-slate-700"><option value="all">All Types</option>{availableTypes.map(type => <option key={type} value={type}>{type}</option>)}</select><button title="Zoom out" onClick={() => setZoom(value => Math.max(0.75, value - 0.1))} className="p-2 border rounded"><Minus className="w-4 h-4" /></button><button title="Zoom in" onClick={() => setZoom(value => Math.min(1.35, value + 0.1))} className="p-2 border rounded"><Plus className="w-4 h-4" /></button><button title="Reset graph" onClick={() => { setSelected(`${entityType || 'complaint'}:${entityId || rootId}`); setTypeFilter('all'); setExpandedTypes([]); setZoom(1) }} className="p-2 border rounded"><RefreshCw className="w-4 h-4" /></button></div>
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_290px] gap-4 mt-4"><div className="overflow-hidden rounded-lg bg-slate-900 min-h-[520px]"><svg viewBox="0 0 940 540" className="w-full h-[520px]" style={{ transform: `scale(${zoom})`, transformOrigin: 'center' }}><defs><filter id="graph-shadow"><feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.3" /></filter></defs>{visibleEdges.map((edge, index) => { const source = positionMap.get(edge.source); const target = positionMap.get(edge.target); if (!source || !target) return null; const highlighted = edge.source === rootNode?.id || edge.target === rootNode?.id; return <g key={`${edge.source}-${edge.target}-${index}`}><path d={`M ${source.x} ${source.y} Q ${(source.x + target.x) / 2} ${(source.y + target.y) / 2 - 24} ${target.x} ${target.y}`} fill="none" stroke={highlighted ? '#67e8f9' : '#475569'} strokeWidth={highlighted ? 2.5 : 1.2} opacity={highlighted ? 0.95 : 0.45} /><text x={(source.x + target.x) / 2} y={(source.y + target.y) / 2 - 28} fill="#cbd5e1" fontSize="9" textAnchor="middle" opacity={highlighted ? 0.9 : 0}>{edge.type}</text></g> })}{positionedNodes.map(node => { const isRoot = node.level === 'root'; const isAggregate = node.id.startsWith('aggregate-'); return <g key={`${node.type}-${node.id}`} onClick={() => selectNode(node)} className="cursor-pointer" filter={isRoot ? 'url(#graph-shadow)' : undefined}><circle cx={node.x} cy={node.y} r={isRoot ? 42 : isAggregate ? 28 : 25} fill={isAggregate ? '#334155' : nodeColors[node.type] || nodeColors.default} stroke={isRoot ? '#fef08a' : isAggregate ? '#94a3b8' : '#e2e8f0'} strokeWidth={isRoot ? 5 : 1.5} strokeDasharray={isAggregate ? '4 3' : undefined} /><text x={node.x} y={node.y + 4} fill="white" fontSize={isRoot ? 11 : 9} textAnchor="middle">{isRoot ? node.type.toUpperCase() : isAggregate ? '+' : node.type.slice(0, 10)}</text>{!isAggregate && <text x={node.x} y={node.y + 43} fill="#e2e8f0" fontSize="10" textAnchor="middle">{shortLabel(node.label, isRoot ? 28 : 20)}</text>}{isAggregate && <text x={node.x} y={node.y + 45} fill="#cbd5e1" fontSize="10" textAnchor="middle">{node.label}</text>}</g> })}</svg></div><aside className={compact ? 'bg-slate-800 rounded p-4' : 'border border-slate-200 rounded-lg p-4'}>{selectedNode ? <DetailPanel node={selectedNode} connectedCount={selectedConnections} relatedComplaintCount={relatedComplaintCount} onExplain={() => setExplanationOpen(true)} /> : <p className="text-sm text-slate-500">Select a node to inspect its connected evidence.</p>}</aside></div>
    </div>
  </div>
}

function DetailPanel({ node, connectedCount, relatedComplaintCount, onExplain }: { node: GraphNode; connectedCount: number; relatedComplaintCount: number; onExplain: () => void }) {
  const type = node.type.toUpperCase()
  return <><p className="text-xs uppercase tracking-wider text-slate-500">{type}</p><h3 className="font-semibold mt-1">{shortLabel(node.label, 32)}</h3><p className="text-sm text-slate-500 mt-2">{connectedCount} direct connections</p><div className="mt-4 space-y-2 text-sm">{type === 'COMPLAINT' && <><p>Customer</p><p>Order</p><p>Policy</p><p>Incident</p><p>Similar complaints: {relatedComplaintCount}</p><p>SLA signals</p></>}{type === 'INCIDENT' && <><p>{relatedComplaintCount} related complaints</p><p>Potential contributing factors</p><p>Confidence: relationship evidence</p></>}{type === 'CUSTOMER' && <><p>Connected complaints and orders</p><p>Customer 360 risk available</p></>}{type !== 'COMPLAINT' && type !== 'INCIDENT' && type !== 'CUSTOMER' && <p>Metadata: {Object.keys(node.metadata || {}).length ? Object.entries(node.metadata || {}).map(([key, value]) => `${key}: ${String(value)}`).join(' · ') : 'No additional metadata available'}</p>}</div><div className="space-y-2 mt-5">{node.type === 'complaint' && <><Link className="block text-center px-3 py-2 rounded bg-blue-600 text-white text-sm" to={`/complaints/${node.id}`}>Open Complaint</Link><Link className="block text-center px-3 py-2 rounded border border-slate-300 text-sm" to={`/intelligence-graph?entity=complaint&id=${node.id}`}>View Decision Trace</Link></>}{node.type === 'customer' && <Link className="block text-center px-3 py-2 rounded bg-blue-600 text-white text-sm" to={`/customers/${node.id}`}>View Customer 360</Link>}{node.type === 'incident' && <Link className="block text-center px-3 py-2 rounded bg-blue-600 text-white text-sm" to={`/incidents/${node.id}`}>View Incident</Link>}<button onClick={onExplain} className="w-full text-center px-3 py-2 rounded border border-slate-300 text-sm flex items-center justify-center gap-2"><Sparkles className="w-4 h-4" /> Explain this network</button></div></>
}

function shortLabel(label: string, length: number) { return label.length > length ? `${label.slice(0, length - 1)}…` : label }
