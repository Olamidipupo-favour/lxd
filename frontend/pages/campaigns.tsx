import { useEffect, useState } from 'react'
import useSWR from 'swr'
import { api } from '../lib/api'
import Nav from '../components/Nav'
import { useAuthGate } from '../lib/authGate'

const fetcher = (url: string) => api.get(url).then(r => r.data)

export default function Campaigns() {
  useAuthGate()
  const { data, mutate } = useSWR('/campaigns/', fetcher)
  const { data: mdata } = useSWR('/mailboxes/', fetcher)
  const [form, setForm] = useState({ name: '', subject_template: '', body_template: '', from_name: '', mailbox_id: '', daily_limit: 1000, throttle_per_hour: 200 })
  const [editingId, setEditingId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState<any>({})
  const [runningId, setRunningId] = useState<string | null>(null)

  async function createOrUpdate() {
    setLoading(true)
    try {
      if (editingId) {
        await api.put(`/campaigns/${editingId}`, form)
        setEditingId(null)
      } else {
        await api.post('/campaigns/', form)
      }
      setForm({ name: '', subject_template: '', body_template: '', from_name: '', mailbox_id: '', daily_limit: 1000, throttle_per_hour: 200 })
      mutate()
    } finally {
      setLoading(false)
    }
  }

  async function edit(id: string) {
    setLoading(true)
    try {
      const res = await api.get(`/campaigns/${id}`)
      setForm({
        name: res.data.name || '',
        subject_template: res.data.subject_template || '',
        body_template: res.data.body_template || '',
        from_name: res.data.from_name || '',
        mailbox_id: res.data.mailbox_id || '',
        daily_limit: res.data.daily_limit || 1000,
        throttle_per_hour: res.data.throttle_per_hour || 200,
      })
      setEditingId(id)
    } finally {
      setLoading(false)
    }
  }

  async function populate(id: string) {
    setLoading(true)
    try {
      await api.post(`/campaigns/${id}/populate`)
      alert('Populated')
    } finally {
      setLoading(false)
    }
  }

  async function start(id: string) {
    setLoading(true)
    setRunningId(id)
    try {
      await api.post(`/campaigns/${id}/start`)
      mutate()
    } finally {
      setLoading(false)
    }
  }

  async function runAll() {
    setLoading(true)
    try {
      await api.post('/campaigns/run-all')
      mutate()
      alert('Started all campaigns')
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error')
    } finally {
      setLoading(false)
    }
  }

  async function remove(id: string) {
    if (!confirm('Delete this campaign?')) return
    setLoading(true)
    try {
      await api.delete(`/campaigns/${id}`)
      mutate()
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!runningId) return
    const interval = setInterval(async () => {
      try {
        const res = await api.get(`/campaigns/${runningId}/progress`)
        setProgress(p => ({ ...p, [runningId]: res.data }))
        if (res.data.status === 'completed' || res.data.status === 'paused') {
          clearInterval(interval)
          setRunningId(null)
          mutate()
        }
      } catch (e) {
        // ignore
      }
    }, 3000)
    return () => clearInterval(interval)
  }, [runningId])

  return (
    <div>
      <Nav />
      <div className="p-6">
        <h1 className="text-2xl mb-4">Campaigns</h1>
        <div className="card mb-4">
          <h3 className="mb-2">{editingId ? 'Edit Campaign' : 'Create Campaign'}</h3>
          <input className="input mb-2" placeholder="Name" value={form.name} onChange={e => setForm({...form, name: e.target.value})} />
          <input className="input mb-2" placeholder="Subject ({{first_name}})" value={form.subject_template} onChange={e => setForm({...form, subject_template: e.target.value})} />
          <textarea className="input mb-2" placeholder="Body (HTML or text). Links auto-click-tracked, pixel auto-added, unsubscribe auto-added" rows={8} value={form.body_template} onChange={e => setForm({...form, body_template: e.target.value})} />
          <input className="input mb-2" placeholder="From Name" value={form.from_name} onChange={e => setForm({...form, from_name: e.target.value})} />
          <select className="input mb-2" value={form.mailbox_id} onChange={e => setForm({...form, mailbox_id: e.target.value})}>
            <option value="">Any active mailbox (rotate)</option>
            {(mdata?.items || []).map((m: any) => <option key={m.id} value={m.id}>{m.email}</option>)}
          </select>
          <div className="grid grid-cols-2 gap-2 mb-2">
            <input className="input" type="number" placeholder="Daily Limit" value={form.daily_limit} onChange={e => setForm({...form, daily_limit: Number(e.target.value)})} />
            <input className="input" type="number" placeholder="Throttle Per Hour" value={form.throttle_per_hour} onChange={e => setForm({...form, throttle_per_hour: Number(e.target.value)})} />
          </div>
          <div className="flex gap-2">
            <button className="btn" disabled={loading} onClick={createOrUpdate}>{loading ? 'Saving...' : (editingId ? 'Update' : 'Create')}</button>
            {editingId && <button className="btn" onClick={() => { setEditingId(null); setForm({ name: '', subject_template: '', body_template: '', from_name: '', mailbox_id: '', daily_limit: 1000, throttle_per_hour: 200 }) }}>Cancel</button>}
            <button className="btn" disabled={loading} onClick={runAll}>Run All Campaigns</button>
          </div>
        </div>
        <div className="card">
          <table className="w-full text-sm">
            <thead><tr className="text-left"><th>Name</th><th>Status</th><th>Daily Limit</th><th>Progress</th><th>Actions</th></tr></thead>
            <tbody>
              {(data?.items || []).map((c: any) => {
                const p = progress[c.id]
                return (
                  <tr key={c.id} className="border-t border-gray-800">
                    <td className="py-2">{c.name}</td>
                    <td>{c.status}</td>
                    <td>{c.daily_limit}</td>
                    <td>
                      {p ? (
                        <div>
                          <div className="text-xs">{p.sent}/{p.total} sent ({p.progress}%)</div>
                          <div className="w-full bg-gray-700 h-1 mt-1"><div className="bg-green-500 h-1" style={{ width: p.progress + '%' }}></div></div>
                        </div>
                      ) : '-'}
                    </td>
                    <td className="flex gap-1 flex-wrap">
                      <button className="btn" disabled={loading} onClick={() => edit(c.id)}>Edit</button>
                      <button className="btn" disabled={loading} onClick={() => populate(c.id)}>Populate</button>
                      <button className="btn" disabled={loading || c.status === 'running'} onClick={() => start(c.id)}>{c.status === 'running' ? 'Running' : 'Start'}</button>
                      <button className="btn" disabled={loading || c.status === 'running'} onClick={() => remove(c.id)}>Delete</button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
