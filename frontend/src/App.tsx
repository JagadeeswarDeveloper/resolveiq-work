import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import ComplaintList from './pages/ComplaintList'
import ComplaintDetail from './pages/ComplaintDetail'
import IncidentList from './pages/IncidentList'
import IncidentDetail from './pages/IncidentDetail'
import CustomerDetail from './pages/CustomerDetail'
import Approval from './pages/Approval'
import KnowledgeCenter from './pages/KnowledgeCenter'
import './index.css'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/complaints" element={<ComplaintList />} />
            <Route path="/complaints/:id" element={<ComplaintDetail />} />
            <Route path="/incidents" element={<IncidentList />} />
            <Route path="/incidents/:id" element={<IncidentDetail />} />
            <Route path="/customers/:id" element={<CustomerDetail />} />
            <Route path="/approval" element={<Approval />} />
            <Route path="/knowledge" element={<KnowledgeCenter />} />
          </Routes>
        </Layout>
      </Router>
    </QueryClientProvider>
  )
}

export default App
