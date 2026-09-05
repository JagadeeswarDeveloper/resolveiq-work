import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { customerAPI } from '../lib/api'

export default function CustomerDetail() {
  const { id } = useParams<{ id: string }>()
  const customer = useQuery({ queryKey: ['customer', id], queryFn: () => customerAPI.get(id!).then(r => r.data) })
  if (customer.isLoading) return <p>Loading customer...</p>
  if (!customer.data) return <p>Customer not found.</p>
  return <div className="bg-white p-6 rounded-lg shadow space-y-2"><h1 className="text-3xl font-bold">{customer.data.name}</h1><p>{customer.data.email}</p><p>Tier: {customer.data.tier}</p><p>Complaints: {customer.data.complaints_count}</p><p>Lifetime value: ${customer.data.lifetime_value.toFixed(2)}</p></div>
}