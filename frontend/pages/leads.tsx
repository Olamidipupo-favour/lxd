import { useState } from 'react'
import useSWR from 'swr'
import api from '../lib/api'
import Nav from '../components/Nav'
import { useAuthGate } from '../lib/authGate'

const fetcher = (url: string) => api.get(url).then(r => r.data)

export default function Leads() {
  useAuthGate()
  const { data, mutate } = useSWR('/leads/?limit=500', fetcher)
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [q, setQ] = useState('')

  async function upload() {
    if (!file) return
    setLoading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      await api.post('/leads/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setFile(null)
      mutate()
    } finally {
      setLoading(false)
    }
  }

  function toggle(id: string) {
    const s = new Set(selected)
    if (s.has(id)) s.delete(id)
    else s.add(id)
    setSelected(s)
  }

  function toggleAll() {
    if (selected.size === (items.length || 0)) {
      setSelected(new Set())
    } else {
      setSelected(new Set(items.map((l: any) => l.id)))
    }
  }

  async function bulk(action: string) {
    if (selected.size === 0) return alert('Select leads first')
    if (action === 'delete' && !confirm('Delete selected leads?')) return
    setLoading(true)
    try {
      await api.post('/leads/bulk', { lead_ids: Array.from(selected), action })
      setSelected(new Set())
      mutate()
    } finally {
      setLoading(false)
    }
  }

  const items = (data?.items || []).filter((l: any) => {
    if (!q) return true
    const s = q.toLowerCase()
    return l.email?.toLowerCase().includes(s) || l.first_name?.toLowerCase().includes(s) || l.last_name?.toLowerCase().includes(s) || l.company?.toLowerCase().includes(s)
  })

  return (
    <div>
      <Nav />
      <div className="p-6">
        <h1 className="text-2xl mb-4">Leads</h1>
        <div className="card mb-4">
          <h3 className="mb-2">CSV Upload</h3>
          <p className="text-sm text-gray-400 mb-2">Columns: email, first_name, last_name, company, title, website, phone</p>
          <div className="flex gap-2 items-center">
            <input type="file" accept=".csv" onChange={e => setFile(e.target.files?.[0] || null)} />
            <button className="btn" onClick={upload} disabled={!file || loading}>{loading ? 'Uploading...' : 'Upload'}</button>
          </div>
        </div>
        <div className="card mb-4">
          <div className="flex gap-2 items-center mb-2">
            <input className="input flex-1" placeholder="Search leads..." value={q} onChange={e => setQ(e.target.value)} />
            <select className="input" onChange={e => { const v = e.target.value; if (v) bulk(v); e.target.value = ''; }} disabled={loading || selected.size === 0}>
              <option value="">Bulk Actions ({selected.size})</option>
              <option value="activate">Activate</option>
              <option value="suppress">Suppress</option>
              <option value="unsuppress">Unsuppress</option>
              <option value="delete">Delete</option>
            </select>
          </div>
          <table className="w-full text-sm">
            <thead><tr className="text-left"><th><input type="checkbox" checked={selected.size === items.length && items.length > 0} onChange={toggleAll} /></th><th>Email</th><th>Name</th><th>Company</th><th>Title</th><th>Status</th><th>Source</th></tr></thead>
            <tbody>
              {items.map((l: any) => (
                <tr key={l.id} className="border-t border-gray-800">
                  <td className="py-2"><input type="checkbox" checked={selected.has(l.id)} onChange={() => toggle(l.id)} /></td>
                  <td>{l.email}</td>
                  <td>{[l.first_name, l.last_name].filter(Boolean).join(' ')}</td>
                  <td>{l.company}</td>
                  <td>{l.title}</td>
                  <td>{l.status}</td>
                  <td>{l.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
