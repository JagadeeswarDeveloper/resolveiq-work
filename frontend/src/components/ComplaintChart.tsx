import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface DataPoint {
  date: string
  count: number
}

export default function ComplaintChart({ data }: { data: DataPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data || []}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Bar dataKey="count" fill="#3b82f6" />
      </BarChart>
    </ResponsiveContainer>
  )
}
