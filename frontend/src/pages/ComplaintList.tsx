import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { complaintAPI, type ComplaintStatus } from '../lib/api'
import { Link, useNavigate } from 'react-router-dom'
import { ChevronRight, Plus, X } from 'lucide-react'

export default function ComplaintList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [skip, setSkip] = useState(0)
  const [status, setStatus] = useState<ComplaintStatus | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [customerEmail, setCustomerEmail] = useState('')
  const [channel, setChannel] = useState<'email' | 'ticket' | 'web_form' | 'chat' | 'phone' | 'social_media'>('email')
  const [rawText, setRawText] = useState('')

  const { data: complaints, isLoading } = useQuery({
    queryKey: ['complaints', skip, status],
    queryFn: () => complaintAPI.list(skip, 50, status || undefined).then(r => r.data),
  })

  const createMutation = useMutation({
    mutationFn: () => complaintAPI.create({ customer_email: customerEmail, channel, raw_text: rawText }),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['complaints'] })
      setShowCreateForm(false)
      setCustomerEmail('')
      setRawText('')
      navigate(`/complaints/${response.data.id}`)
    },
  })

  if (isLoading) {
    return <div className="text-center py-12">Loading complaints...</div>
  }

  const getSeverityColor = (status: string) => {
      if (status === 'escalated') return 'bg-red-100 text-red-800'
      if (status === 'investigating') return 'bg-yellow-100 text-yellow-800'
      if (status === 'resolved') return 'bg-green-100 text-green-800'
    return 'bg-blue-100 text-blue-800'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Complaints</h1>
          <p className="text-gray-600 mt-2">Manage and resolve customer complaints</p>
        </div>
        <button
          type="button"
          onClick={() => setShowCreateForm(value => !value)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
        >
          {showCreateForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
          {showCreateForm ? 'Close' : 'New complaint'}
        </button>
      </div>

      {showCreateForm && (
        <form
          onSubmit={(event) => {
            event.preventDefault()
            createMutation.mutate()
          }}
          className="bg-white p-6 rounded-lg shadow space-y-4"
        >
          <h2 className="text-lg font-semibold">Create complaint</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label className="text-sm font-medium text-gray-700">
              Customer email
              <input
                required
                type="email"
                value={customerEmail}
                onChange={(event) => setCustomerEmail(event.target.value)}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg font-normal"
                placeholder="customer@example.com"
              />
            </label>
            <label className="text-sm font-medium text-gray-700">
              Channel
              <select
                value={channel}
                onChange={(event) => setChannel(event.target.value as typeof channel)}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg font-normal"
              >
                <option value="email">Email</option>
                <option value="ticket">Ticket</option>
                <option value="web_form">Web form</option>
                <option value="chat">Chat</option>
                <option value="phone">Phone</option>
                <option value="social_media">Social media</option>
              </select>
            </label>
          </div>
          <label className="block text-sm font-medium text-gray-700">
            Complaint
            <textarea
              required
              rows={4}
              value={rawText}
              onChange={(event) => setRawText(event.target.value)}
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg font-normal"
              placeholder="Describe what happened and what the customer needs."
            />
          </label>
          {createMutation.isError && <p className="text-sm text-red-600">Could not create the complaint. Check the details and try again.</p>}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-60"
            >
              {createMutation.isPending ? 'Creating...' : 'Create complaint'}
            </button>
          </div>
        </form>
      )}

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow">
        <select
          value={status || ''}
          onChange={(e) => {
            const value = e.target.value
            setStatus(value ? value as ComplaintStatus : null)
            setSkip(0)
          }}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Statuses</option>
          <option value="received">Received</option>
          <option value="investigating">Investigating</option>
          <option value="resolved">Resolved</option>
          <option value="escalated">Escalated</option>
        </select>
      </div>

      {/* Complaints List */}
      <div className="space-y-3">
        {complaints?.map((complaint: any) => (
          <Link
            key={complaint.id}
            to={`/complaints/${complaint.id}`}
            className="block bg-white p-4 rounded-lg shadow hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`px-2 py-1 rounded text-sm font-medium ${getSeverityColor(complaint.status)}`}>
                    {complaint.status}
                  </span>
                  <span className="text-xs text-gray-500">{complaint.channel}</span>
                </div>
                <p className="text-gray-900 font-medium line-clamp-2">{complaint.raw_text}</p>
                <p className="text-xs text-gray-500 mt-1">
                  ID: {complaint.id.substring(0, 8)}... | Created: {new Date(complaint.created_at).toLocaleDateString()}
                </p>
              </div>
              <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
            </div>
          </Link>
        ))}
      </div>

      {/* Pagination */}
      <div className="flex gap-2 justify-center">
        <button
          onClick={() => setSkip(Math.max(0, skip - 50))}
          disabled={skip === 0}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50"
        >
          Previous
        </button>
        <button
          onClick={() => setSkip(skip + 50)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg"
        >
          Next
        </button>
      </div>
    </div>
  )
}
