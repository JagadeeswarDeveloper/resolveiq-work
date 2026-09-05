import { Link, useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Play, Plus } from 'lucide-react'
import { complaintAPI } from '../lib/api'

export default function QuickActions() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const demoMutation = useMutation({
    mutationFn: complaintAPI.createDemo,
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] })
      queryClient.invalidateQueries({ queryKey: ['complaints'] })
      navigate(`/complaints/${response.data.id}`)
    },
  })

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          to="/complaints"
          className="p-4 border-2 border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
        >
          <Play className="w-6 h-6 text-blue-600 mb-2" />
          <p className="font-medium text-gray-900">View All Complaints</p>
          <p className="text-sm text-gray-600">Browse complaint queue</p>
        </Link>
        <Link
          to="/incidents"
          className="p-4 border-2 border-purple-200 rounded-lg hover:bg-purple-50 transition-colors"
        >
          <Plus className="w-6 h-6 text-purple-600 mb-2" />
          <p className="font-medium text-gray-900">View Incidents</p>
          <p className="text-sm text-gray-600">Operational pattern analysis</p>
        </Link>
        <button
          type="button"
          onClick={() => demoMutation.mutate()}
          disabled={demoMutation.isPending}
          className="p-4 border-2 border-green-200 rounded-lg hover:bg-green-50 transition-colors cursor-pointer text-left disabled:opacity-60"
        >
          <Play className="w-6 h-6 text-green-600 mb-2" />
          <p className="font-medium text-gray-900">Run Demo</p>
          <p className="text-sm text-gray-600">{demoMutation.isPending ? 'Running workflow...' : 'Submit test complaint'}</p>
          {demoMutation.isError && <p className="text-sm text-red-600 mt-1">Demo failed. Try again.</p>}
        </button>
      </div>
    </div>
  )
}
