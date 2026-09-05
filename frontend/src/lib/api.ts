import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

export type ComplaintStatus =
  | 'received' | 'normalized' | 'classified' | 'prioritized'
  | 'investigating' | 'resolution_proposed' | 'pending_approval'
  | 'approved' | 'resolved' | 'escalated' | 'rejected' | 'closed'
export type Channel = 'email' | 'ticket' | 'web_form' | 'chat' | 'phone' | 'social_media'
export type Complaint = {
  id: string
  customer_id: string
  channel: Channel
  raw_text: string
  status: ComplaintStatus
  created_at: string
  updated_at?: string
  analysis?: { category?: string; sentiment?: string; severity?: string; summary?: string }
  priority?: { priority_score?: number; priority_level?: string; reasons?: string[] }
  arc_events?: { arc_stage: string; status: string; timestamp: string }[]
  resolution_recommendation?: {
    recommended_action?: string
    customer_response?: string
    compensation?: { type?: string; amount?: number; reason?: string }
    reasoning_summary?: string
    confidence?: number
    requires_human_review?: boolean
    policy_evidence?: PolicyEvidence[]
    policy_sources?: string[]
    policy_confidence?: number
  }
  incidents?: Incident[]
}
export type DashboardSummary = { total_complaints: number; open_complaints: number; high_priority_complaints: number; avg_resolution_time_hours: number; sla_breach_rate: number; sla_breaches: number; auto_resolution_rate: number; human_approval_rate: number; active_incidents: number }
export type WorkflowRun = { workflow_id: string; complaint_id: string; status: string; current_node: string; state: Record<string, any>; retry_count: number; last_error?: string }
export type PolicyEvidence = { document: string; content: string; score: number; metadata: { section?: string; [key: string]: unknown } }
export type KnowledgeDocument = { id: string; title: string; document_type?: string; category?: string; version: number; status?: string; source?: string; created_at: string; updated_at: string; chunks: { id: string; chunk_index: number; content: string; chunk_metadata?: Record<string, unknown> }[] }
export type ComplaintCreate = {
  customer_id?: string
  customer_email?: string
  channel: Channel
  raw_text: string
  language?: string
  metadata?: Record<string, unknown>
}
export type Incident = {
  id: string
  title: string
  description?: string
  status: string
  complaint_count: number
  confidence: number
  detected_at: string
  created_at: string
  affected_regions?: string[]
  evidence?: Record<string, unknown>
  suspected_root_cause?: string
  potential_root_cause?: string
  evidence_summary?: string
  severity?: string
  affected_customers_count?: number
  high_priority_count?: number
  sla_breach_count?: number
  estimated_business_impact?: number
  regions_affected?: number
  products_affected?: number
  baseline_volume?: number
  current_volume?: number
  volume_change_percent?: number
}
export type Customer = { id: string; name: string; email: string; tier?: string; account_status?: string; complaints_count: number; lifetime_value: number }

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const complaintAPI = {
  list: (skip = 0, limit = 50, status?: ComplaintStatus) => api.get<Complaint[]>('/complaints', { params: { skip, limit, status } }),
  get: (id: string) => api.get<Complaint>(`/complaints/${id}`),
  create: (data: ComplaintCreate) => api.post<Complaint>('/complaints', data),
  createDemo: () => api.post<Complaint>('/complaints/demo'),
  analyze: (id: string) => api.post(`/complaints/${id}/analyze`),
  prioritize: (id: string) => api.post(`/complaints/${id}/prioritize`),
  investigate: (id: string) => api.post(`/complaints/${id}/investigate`),
  resolve: (id: string) => api.post(`/complaints/${id}/resolve`),
  route: (id: string) => api.post(`/complaints/${id}/route`),
  approve: (id: string) => api.post(`/complaints/${id}/approve`),
  escalate: (id: string) => api.post(`/complaints/${id}/escalate`),
}

export const workflowAPI = {
  run: (complaintId: string) => api.post<WorkflowRun>(`/workflows/complaints/${complaintId}/run`),
  get: (workflowId: string) => api.get<WorkflowRun>(`/workflows/${workflowId}`),
  resume: (workflowId: string, approved = true) => api.post<WorkflowRun>(`/workflows/${workflowId}/resume`, null, { params: { approved } }),
  events: (workflowId: string) => api.get(`/workflows/${workflowId}/events`),
}

export const dashboardAPI = {
  summary: () => api.get('/dashboard/summary'),
  trends: (days = 7) => api.get('/dashboard/trends', { params: { days } }),
  categories: () => api.get('/dashboard/categories'),
  severity: () => api.get('/dashboard/severity-distribution'),
  channels: () => api.get('/dashboard/channel-distribution'),
}

export const incidentAPI = {
  list: (skip = 0, limit = 50) => api.get<Incident[]>('/incidents', { params: { skip, limit } }),
  get: (id: string) => api.get<Incident>(`/incidents/${id}`),
  complaints: (id: string) => api.get<{ success: boolean; data?: { complaints: Complaint[] } }>(`/incidents/${id}/complaints`),
  detect: () => api.post<Incident[]>('/incidents/detect'),
  refresh: (id: string) => api.post<Incident[]>(`/incidents/${id}/refresh`),
  evidence: (id: string) => api.get(`/incidents/${id}/evidence`),
}

export const customerAPI = {
  list: (skip = 0, limit = 50) => api.get('/customers', { params: { skip, limit } }),
  get: (id: string) => api.get<Customer>(`/customers/${id}`),
  complaints: (id: string) => api.get(`/customers/${id}/complaints`),
  orders: (id: string) => api.get(`/customers/${id}/orders`),
}

export const knowledgeAPI = {
  list: () => api.get<KnowledgeDocument[]>('/knowledge/documents'),
  create: (data: { title: string; content: string; document_type?: string; category?: string; version?: number; source?: string }) => api.post<KnowledgeDocument>('/knowledge/documents', data),
  delete: (id: string) => api.delete(`/knowledge/documents/${id}`),
  ingest: (id: string) => api.post<KnowledgeDocument>(`/knowledge/documents/${id}/ingest`),
  search: (query: string) => api.get<{ query: string; results: PolicyEvidence[] }>('/knowledge/search', { params: { q: query } }),
}
