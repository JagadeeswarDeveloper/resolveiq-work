import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { complaintAPI } from '../lib/api'

export default function Approval() {
  const pending = useQuery({
    queryKey: ['approval-queue'],
    queryFn: () => complaintAPI.list(0, 100, 'pending_approval').then(response => response.data),
  })
  return <div className="space-y-4"><h1 className="text-3xl font-bold">Approval</h1><p className="text-gray-600">Complaints requiring human review.</p>{pending.isLoading && <p>Loading approvals...</p>}<div className="space-y-2">{pending.data?.map(complaint => <Link className="block bg-white p-4 rounded-lg shadow" to={`/complaints/${complaint.id}`} key={complaint.id}><p className="font-medium">{complaint.raw_text}</p><p className="text-sm text-gray-500">{complaint.id}</p></Link>)}{pending.data?.length === 0 && <p>No complaints require approval.</p>}</div></div>
}