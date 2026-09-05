import { useQuery } from '@tanstack/react-query'
import { incidentAPI } from '../lib/api'
import { AlertTriangle } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { Incident } from '../lib/api'

export default function IncidentList() {
  const { data: incidents, isLoading } = useQuery({
    queryKey: ['incidents'],
    queryFn: () => incidentAPI.list().then(r => r.data),
  })

  if (isLoading) {
    return <div className="text-center py-12">Loading incidents...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Incidents</h1>
        <p className="text-gray-600 mt-2">Operational incidents detected from complaint patterns</p>
      </div>

      <div className="space-y-4">
        {incidents?.length === 0 ? (
          <div className="bg-white p-8 rounded-lg shadow text-center">
            <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600">No incidents detected yet</p>
          </div>
        ) : (
          incidents?.map((incident: Incident) => (
            <Link to={`/incidents/${incident.id}`} key={incident.id} className="block bg-white p-6 rounded-lg shadow hover:shadow-md">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{incident.title}</h3>
                  <p className="text-gray-600 mt-1">{incident.description}</p>
                  <div className="flex gap-4 mt-4 text-sm text-gray-600">
                    <span>Complaints: {incident.complaint_count}</span>
                    <span>Confidence: {(incident.confidence * 100).toFixed(0)}%</span>
                    <span>Status: {incident.status}</span>
                  </div>
                  {incident.suspected_root_cause && (
                    <div className="mt-3">
                      <p className="text-sm font-medium text-gray-700">
                        Potential Root Cause:
                      </p>
                      <p className="text-sm text-gray-600">{incident.suspected_root_cause}</p>
                    </div>
                  )}
                </div>
                <span className={`
                  px-3 py-1 rounded-full text-sm font-medium whitespace-nowrap
                  ${incident.status === 'DETECTED' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}
                `}>
                  {incident.status}
                </span>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  )
}
