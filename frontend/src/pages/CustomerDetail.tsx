import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { customerAPI } from '../lib/api'
import { Customer360Panel } from '../components/IntelligencePanels'

export default function CustomerDetail() {
  const { id } = useParams<{ id: string }>()
  const customer = useQuery({ queryKey: ['customer', id], queryFn: () => customerAPI.get(id!).then(r => r.data) })
  if (customer.isLoading) return <p>Loading customer...</p>
  if (!customer.data) return <p>Customer not found.</p>
  return <div className="space-y-6"><div><h1 className="text-3xl font-bold">{customer.data.name}</h1><p className="text-slate-600">{customer.data.email} · {customer.data.tier || 'Tier unavailable'}</p></div><Customer360Panel customerId={customer.data.id} /><div className="bg-white p-6 rounded-lg shadow space-y-2"><h2 className="text-lg font-semibold">Account summary</h2><p>Complaints: {customer.data.complaints_count}</p><p>Lifetime value: ${customer.data.lifetime_value.toFixed(2)}</p></div></div>
}