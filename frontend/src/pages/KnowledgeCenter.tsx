import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { knowledgeAPI, type KnowledgeDocument } from '../lib/api'

export default function KnowledgeCenter() {
  const [query, setQuery] = useState('late delivery compensation')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [category, setCategory] = useState('')
  const [documentType, setDocumentType] = useState('policy')
  const [saveMessage, setSaveMessage] = useState('')
  const queryClient = useQueryClient()
  const documents = useQuery({ queryKey: ['knowledge-documents'], queryFn: () => knowledgeAPI.list().then(response => response.data) })
  const results = useQuery({ queryKey: ['knowledge-search', query], queryFn: () => knowledgeAPI.search(query).then(response => response.data.results), enabled: query.length > 1 })
  const ingest = useMutation({
    mutationFn: (id: string) => knowledgeAPI.ingest(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['knowledge-documents'] }),
  })
  const remove = useMutation({
    mutationFn: (id: string) => knowledgeAPI.delete(id),
    onSuccess: (_response, id) => {
      queryClient.setQueryData<KnowledgeDocument[]>(['knowledge-documents'], current => (current || []).filter(document => document.id !== id))
      queryClient.invalidateQueries({ queryKey: ['knowledge-documents'] })
    },
  })
  const create = useMutation({
    mutationFn: () => knowledgeAPI.create({ title, content, category: category || undefined, document_type: documentType }),
    onSuccess: (response) => {
      queryClient.setQueryData<KnowledgeDocument[]>(['knowledge-documents'], (current = []) => [response.data, ...current.filter(document => document.id !== response.data.id)])
      queryClient.invalidateQueries({ queryKey: ['knowledge-documents'] })
      setTitle('')
      setContent('')
      setCategory('')
      setShowCreateForm(false)
      setSaveMessage(`Saved "${response.data.title}". Click Ingest to make it searchable.`)
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-start justify-between gap-4">
          <div><h1 className="text-3xl font-bold text-gray-900">Knowledge Center</h1><p className="text-gray-600 mt-2">Enterprise policies used to ground recommendations.</p></div>
          <button type="button" onClick={() => setShowCreateForm(value => !value)} className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700">{showCreateForm ? 'Close' : 'Add policy'}</button>
        </div>
      </div>
      {showCreateForm && <form onSubmit={event => { event.preventDefault(); create.mutate() }} className="bg-white p-6 rounded-lg shadow space-y-4">
        <h2 className="text-lg font-semibold">Add policy or knowledge document</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <label className="text-sm font-medium text-gray-700">Title<input required value={title} onChange={event => setTitle(event.target.value)} className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg font-normal" placeholder="Returns policy" /></label>
          <label className="text-sm font-medium text-gray-700">Category<input value={category} onChange={event => setCategory(event.target.value)} className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg font-normal" placeholder="refund" /></label>
          <label className="text-sm font-medium text-gray-700">Type<select value={documentType} onChange={event => setDocumentType(event.target.value)} className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg font-normal"><option value="policy">Policy</option><option value="faq">FAQ</option><option value="sop">SOP</option><option value="runbook">Runbook</option></select></label>
        </div>
        <label className="block text-sm font-medium text-gray-700">Policy content<textarea required rows={5} value={content} onChange={event => setContent(event.target.value)} className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg font-normal" placeholder="State the rule, eligibility, limits, and required support action." /></label>
        {create.isError && <p className="text-sm text-red-600">Could not add the policy. Please try again.</p>}
        <div className="flex justify-end"><button type="submit" disabled={create.isPending} className="px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-60">{create.isPending ? 'Adding...' : 'Add policy'}</button></div>
      </form>}
      {saveMessage && <div role="status" className="bg-green-50 border border-green-200 text-green-800 p-4 rounded-lg">{saveMessage}</div>}
      <div className="bg-white p-6 rounded-lg shadow">
        <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="knowledge-search">Search policy evidence</label>
        <input id="knowledge-search" value={query} onChange={event => setQuery(event.target.value)} className="w-full px-3 py-2 border rounded" />
        <div className="mt-4 space-y-3">
          {results.data?.map((result, index) => (
            <div key={`${result.document}-${index}`} className="border-l-4 border-blue-500 pl-3">
              <p className="font-medium">{result.document}</p>
              <p className="text-sm text-gray-500">{result.metadata.section || 'Policy section'} · {(result.score * 100).toFixed(0)}% relevant</p>
              <p className="text-sm mt-1">{result.content}</p>
            </div>
          ))}
        </div>
      </div>
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b font-semibold">Documents</div>
        {documents.isLoading && <p className="p-4 text-gray-500">Loading knowledge documents...</p>}
        {documents.isError && <p className="p-4 text-red-600">Could not load knowledge documents. Check that the API is running.</p>}
        {!documents.isLoading && !documents.isError && !documents.data?.length && <p className="p-4 text-gray-500">No policies have been added yet.</p>}
        <div className="divide-y">
          {documents.data?.map(document => (
            <div className="p-4 flex items-center justify-between" key={document.id}>
              <div><p className="font-medium">{document.title}</p><p className="text-sm text-gray-500">{document.document_type} · v{document.version} · {document.chunks.length} chunks</p></div>
              <div className="flex items-center gap-3"><span className="text-sm text-green-700">{document.status}</span><button onClick={() => ingest.mutate(document.id)} disabled={ingest.isPending || remove.isPending} className="px-3 py-1 border rounded text-sm">Ingest</button><button type="button" onClick={() => { if (window.confirm(`Delete policy "${document.title}"?`)) remove.mutate(document.id) }} disabled={remove.isPending} className="px-3 py-1 border border-red-300 text-red-700 rounded text-sm hover:bg-red-50">Delete</button></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
