import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { complaintAPI, workflowAPI } from '../lib/api'
import { Link } from 'react-router-dom'
import { Play, AlertCircle, TrendingUp } from 'lucide-react'
import { Customer360Panel, CriticPanel, DecisionTracePanel, GraphContextPanel } from '../components/IntelligencePanels'

export default function ComplaintDetail() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [loadingStage, setLoadingStage] = useState<string | null>(null)
  const [workflowId, setWorkflowId] = useState<string | null>(null)
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const refreshComplaint = () => {
    queryClient.invalidateQueries({ queryKey: ['complaint', id] })
    queryClient.invalidateQueries({ queryKey: ['complaints'] })
  }

  const { data: complaint, isLoading } = useQuery({
    queryKey: ['complaint', id],
    queryFn: () => complaintAPI.get(id!).then(r => r.data),
  })

  const { data: workflowEvents } = useQuery({
    queryKey: ['workflow-events', workflowId],
    queryFn: () => workflowAPI.events(workflowId!).then(r => r.data),
    enabled: Boolean(workflowId),
  })

  const analyzeMutation = useMutation({
    mutationFn: () => complaintAPI.analyze(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['complaint', id] })
      setLoadingStage(null)
    },
  })

  const prioritizeMutation = useMutation({
    mutationFn: () => complaintAPI.prioritize(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['complaint', id] })
      setLoadingStage(null)
    },
  })

  const investigateMutation = useMutation({
    mutationFn: () => complaintAPI.investigate(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['complaint', id] })
      setLoadingStage(null)
    },
  })

  const resolveMutation = useMutation({
    mutationFn: () => complaintAPI.resolve(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['complaint', id] })
      setLoadingStage(null)
    },
  })

  const approveMutation = useMutation({
    mutationFn: () => complaintAPI.approve(id!),
    onSuccess: (response) => {
      refreshComplaint()
      setActionMessage({ type: 'success', text: response.data.message || 'Complaint approved and resolved.' })
      setLoadingStage(null)
    },
    onError: () => {
      setActionMessage({ type: 'error', text: 'Approval failed. Please try again.' })
      setLoadingStage(null)
    },
  })

  const escalateMutation = useMutation({
    mutationFn: () => complaintAPI.escalate(id!),
    onSuccess: (response) => {
      refreshComplaint()
      setActionMessage({ type: 'success', text: response.data.message || 'Complaint escalated.' })
      setLoadingStage(null)
    },
    onError: () => {
      setActionMessage({ type: 'error', text: 'Escalation failed. Please try again.' })
      setLoadingStage(null)
    },
  })

  const workflowMutation = useMutation({
    mutationFn: () => workflowAPI.run(id!),
    onSuccess: (response) => {
      setWorkflowId(response.data.workflow_id)
      queryClient.invalidateQueries({ queryKey: ['complaint', id] })
      setLoadingStage(null)
    },
  })

  const resumeMutation = useMutation({
    mutationFn: () => workflowAPI.resume(workflowId!, true),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['complaint', id] })
      setLoadingStage(null)
    },
  })

  if (isLoading) return <div className="text-center py-12">Loading...</div>
  if (!complaint) return <div className="text-center py-12">Complaint not found</div>

  const arcStages = [
    { name: 'capture', label: 'Capture' },
    { name: 'unify', label: 'Unify' },
    { name: 'understand', label: 'Understand' },
    { name: 'prioritize', label: 'Prioritize' },
    { name: 'investigate', label: 'Investigate' },
    { name: 'reason', label: 'Reason' },
    { name: 'resolve', label: 'Resolve' },
  ]

  const completedStages = [...(complaint.arc_events?.map((e: any) => e.arc_stage) || []), ...(workflowEvents?.map((event: any) => event.node.toLowerCase()) || [])]
  const workflowStages = ['capture', 'unify', 'understand', 'prioritize', 'investigate', 'reason', 'critic', 'supervisor', 'resolve', 'learn']

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Complaint #{complaint.id.substring(0, 8)}</h1>
        <div className="flex gap-4 mt-2">
          <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
            {complaint.status}
          </span>
          <span className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm font-medium">
            {complaint.channel}
          </span>
        </div>
      </div>

      <div className="bg-slate-900 p-6 rounded-lg shadow text-white">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Workflow Status</h2>
          <button className="px-3 py-2 rounded bg-cyan-500 text-slate-950 font-semibold disabled:opacity-50" disabled={workflowMutation.isPending} onClick={() => { setLoadingStage('workflow'); workflowMutation.mutate() }}>
            {workflowMutation.isPending ? 'Running...' : 'Run orchestrator'}
          </button>
        </div>
        <div className="grid grid-cols-4 md:grid-cols-8 gap-2">
          {workflowStages.map(stage => <div key={stage} className={`p-2 rounded text-center text-xs ${completedStages.includes(stage) ? 'bg-emerald-500/80' : 'bg-slate-700'}`}>
            <div className="text-base">{completedStages.includes(stage) ? '✓' : '○'}</div>
            {stage.toUpperCase()}
          </div>)}
        </div>
        {complaint.status === 'pending_approval' && workflowId && <button className="mt-4 px-4 py-2 rounded bg-emerald-500 text-slate-950 font-semibold" disabled={resumeMutation.isPending} onClick={() => resumeMutation.mutate()}>
          {resumeMutation.isPending ? 'Approving...' : 'Approve and resolve'}
        </button>}
      </div>

      {workflowEvents?.length ? <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Agent Activity</h2>
        <div className="space-y-3">
          {workflowEvents.map((event: any) => <div key={`${event.node}-${event.timestamp}`} className="flex items-center justify-between gap-4 border-b border-gray-100 pb-3">
            <div><p className="font-medium">{event.agent_or_tool}</p><p className="text-sm text-gray-500">{event.node} · {event.status}</p></div>
            <span className="text-sm text-gray-500">{event.duration_ms ?? 0} ms</span>
          </div>)}
        </div>
      </div> : null}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Customer360Panel customerId={complaint.customer_id} />
        <GraphContextPanel complaint={complaint} />
        <CriticPanel complaintId={complaint.id} />
        <DecisionTracePanel complaint={complaint} />
      </div>

      {/* ARC Timeline */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5" />
          Complaint Journey (ARC)
        </h2>
        <div className="flex justify-between gap-2">
          {arcStages.map((stage, idx) => (
            <div key={stage.name} className="flex-1">
              <div className="relative">
                <div className={`
                  py-2 px-3 rounded text-center text-sm font-medium
                  ${completedStages.includes(stage.name)
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-600'
                  }
                `}>
                  {stage.label}
                </div>
                {idx < arcStages.length - 1 && (
                  <div className="absolute top-1/2 -right-2 w-4 h-0.5 bg-gray-300 transform -translate-y-1/2" />
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-3 gap-6">
        {/* Complaint Details */}
        <div className="col-span-2 space-y-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-4">Original Complaint</h2>
            <p className="text-gray-700 leading-relaxed">{complaint.raw_text}</p>
            <p className="text-xs text-gray-500 mt-4">
              Created: {new Date(complaint.created_at).toLocaleString()}
            </p>
          </div>

          {complaint.incidents?.length ? <div className="bg-red-50 border border-red-200 p-6 rounded-lg">
            <h2 className="text-lg font-semibold text-red-900">Related Incident</h2>
            {complaint.incidents.map(incident => <Link key={incident.id} to={`/incidents/${incident.id}`} className="block mt-2 text-red-800 hover:underline">
              {incident.title} · {(incident.confidence * 100).toFixed(0)}% similarity
            </Link>)}
            <p className="text-sm text-red-800 mt-3">Linked by category, similar complaint text, shared context, and the same time window.</p>
          </div> : null}

          {complaint.analysis && (
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-semibold mb-4">Analysis</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Category</p>
                  <p className="text-lg font-medium">{complaint.analysis.category}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Sentiment</p>
                  <p className="text-lg font-medium">{complaint.analysis.sentiment}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Severity</p>
                  <p className="text-lg font-medium">{complaint.analysis.severity}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Summary</p>
                  <p className="text-lg font-medium text-ellipsis overflow-hidden">{complaint.analysis.summary?.substring(0, 50)}</p>
                </div>
              </div>
            </div>
          )}

          {complaint.priority && (
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-semibold mb-4">Priority Assessment</h2>
              <div className="flex items-end gap-4">
                <div>
                  <p className="text-sm text-gray-600">Priority Level</p>
                  <p className="text-2xl font-bold text-red-600">{complaint.priority.priority_level}</p>
                </div>
                <div className="flex-1">
                  <p className="text-sm text-gray-600">Priority Score</p>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-red-600 h-2 rounded-full"
                      style={{ width: `${complaint.priority.priority_score}%` }}
                    />
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{complaint.priority.priority_score}/100</p>
                </div>
              </div>
              {complaint.priority.reasons && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-gray-600">Reasons:</p>
                  <ul className="list-disc list-inside text-sm text-gray-700 mt-2">
                    {complaint.priority.reasons.map((r: string, i: number) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {complaint.resolution_recommendation && (
            <div className="bg-emerald-50 border border-emerald-200 p-6 rounded-lg">
              <h2 className="text-lg font-semibold text-emerald-900 mb-4">Recommended Action</h2>
              <p className="text-xl font-semibold text-emerald-950">
                {complaint.resolution_recommendation.recommended_action || 'Recommendation pending'}
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                <div>
                  <p className="text-sm text-emerald-800">Confidence</p>
                  <p className="font-medium">{complaint.resolution_recommendation.confidence != null ? `${(complaint.resolution_recommendation.confidence * 100).toFixed(0)}%` : 'Not available'}</p>
                </div>
                <div>
                  <p className="text-sm text-emerald-800">Compensation</p>
                  <p className="font-medium">{complaint.resolution_recommendation.compensation ? `${complaint.resolution_recommendation.compensation.type || 'Offer'}${complaint.resolution_recommendation.compensation.amount != null ? ` · $${complaint.resolution_recommendation.compensation.amount}` : ''}` : 'None recommended'}</p>
                </div>
                <div>
                  <p className="text-sm text-emerald-800">Review</p>
                  <p className="font-medium">{complaint.resolution_recommendation.requires_human_review ? 'Human review required' : 'Eligible for automated routing'}</p>
                </div>
              </div>
              {complaint.resolution_recommendation.customer_response && <div className="mt-4"><p className="text-sm text-emerald-800">Customer response</p><p className="text-gray-800 mt-1">{complaint.resolution_recommendation.customer_response}</p></div>}
              {complaint.resolution_recommendation.reasoning_summary && <div className="mt-4"><p className="text-sm text-emerald-800">Decision summary</p><p className="text-gray-800 mt-1">{complaint.resolution_recommendation.reasoning_summary}</p></div>}
            </div>
          )}

          {complaint.resolution_recommendation?.policy_evidence && (
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-semibold mb-4">Policy Evidence</h2>
              <div className="space-y-4">
                {complaint.resolution_recommendation.policy_evidence.map((evidence, index) => (
                  <div key={`${evidence.document}-${index}`} className="border-l-4 border-blue-500 pl-4">
                    <p className="font-medium">{evidence.document}</p>
                    <p className="text-sm text-gray-500">{evidence.metadata.section || 'Policy section'} · Relevance {(evidence.score * 100).toFixed(0)}%</p>
                    <p className="text-sm text-gray-700 mt-1">{evidence.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Actions Sidebar */}
        <div className="space-y-4">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-4">Workflow Actions</h2>
            {actionMessage && (
              <div className={`mb-4 rounded-lg border px-4 py-3 text-sm font-medium ${actionMessage.type === 'success' ? 'border-green-200 bg-green-50 text-green-800' : 'border-red-200 bg-red-50 text-red-800'}`} role="status">
                {actionMessage.text}
              </div>
            )}
            <div className="space-y-2">
              <ActionButton
                label="Analyze"
                onClick={() => {
                  setLoadingStage('analyze')
                  analyzeMutation.mutate()
                }}
                loading={loadingStage === 'analyze'}
                disabled={completeStage('understand', completedStages)}
              />
              <ActionButton
                label="Prioritize"
                onClick={() => {
                  setLoadingStage('prioritize')
                  prioritizeMutation.mutate()
                }}
                loading={loadingStage === 'prioritize'}
                disabled={completeStage('prioritize', completedStages)}
              />
              <ActionButton
                label="Investigate"
                onClick={() => {
                  setLoadingStage('investigate')
                  investigateMutation.mutate()
                }}
                loading={loadingStage === 'investigate'}
                disabled={completeStage('investigate', completedStages)}
              />
              <ActionButton
                label="Generate Resolution"
                onClick={() => {
                  setLoadingStage('resolve')
                  resolveMutation.mutate()
                }}
                loading={loadingStage === 'resolve'}
                disabled={completeStage('reason', completedStages)}
              />
              <ActionButton
                label="Approve"
                onClick={() => {
                  setLoadingStage('approve')
                  approveMutation.mutate()
                }}
                loading={loadingStage === 'approve'}
                variant="success"
              />
              <ActionButton
                label="Escalate"
                onClick={() => {
                  setLoadingStage('escalate')
                  escalateMutation.mutate()
                }}
                loading={loadingStage === 'escalate'}
                variant="danger"
              />
            </div>
          </div>

          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <p className="text-sm text-blue-900">
              <AlertCircle className="w-4 h-4 inline mr-2" />
              Follow the ARC workflow: Capture → Unify → Understand → Prioritize → Investigate → Reason → Resolve
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function ActionButton({
  label,
  onClick,
  loading = false,
  disabled = false,
  variant = 'default',
}: {
  label: string
  onClick: () => void
  loading?: boolean
  disabled?: boolean
  variant?: 'default' | 'success' | 'danger'
}) {
  const baseClass = 'w-full py-2 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2'
  const variantClass = {
    default: 'bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50',
    success: 'bg-green-600 text-white hover:bg-green-700 disabled:opacity-50',
    danger: 'bg-red-600 text-white hover:bg-red-700 disabled:opacity-50',
  }

  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`${baseClass} ${variantClass[variant]}`}
    >
      {loading ? (
        <>
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          Loading...
        </>
      ) : (
        <>
          <Play className="w-4 h-4" />
          {label}
        </>
      )}
    </button>
  )
}

const completeStage = (stage: string, completedStages: any[]) => {
  const stages = ['capture', 'unify', 'understand', 'prioritize', 'investigate', 'reason', 'resolve']
  const stageIdx = stages.indexOf(stage)
  return stageIdx >= 0 && completedStages.includes(stages[Math.min(stageIdx, stages.length - 1)])
}
