import React from 'react'

type Props = {
  title: string
  value: string | number
  icon: React.ReactNode
  color: string
}

export default function StatCard({ title, value, icon, color }: Props) {
  return (
    <div className={`${color} p-6 rounded-lg shadow`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
        </div>
        <div className="text-gray-400">{icon}</div>
      </div>
    </div>
  )
}
