import { useState } from 'react'
import useSWR from 'swr'
import { api } from '../lib/api'
import Nav from '../components/Nav'

const fetcher = (url: string) => api.get(url).then(r => r.data)

export default function Campaigns() {
  const { data, mutate } = useSWR('/campaigns/', fetcher)
  const { data: mdata } = useSWR('/mailboxes/', fetcher)
  const [form, setForm] = useState({ name: '', subject_template: '', body_template: '', from_name: '', mailbox_id: '', daily_limit: 1000, throttle_per_hour: 200 })

  async function create() {
    await api.post('/campaigns/', form)
    setForm({ name: '', subject_template: '', body_template: '', from_name: '', mailbox_id: '', daily_limit: 1000, throttle_per_hour: 200 })
    mutate()
  }

  async function populate(id: string) {
    await api.post(`/campaigns/${id}/populate`)
    alert('Populated')
  }

  async function run(id: string) {
    // runs via internal endpoint; for manual test may need cron secret - but admin can call if we expose; our route requires header, skip for now
    alert('Use GitHub Actions or call with x-cron-secret')
  }

  return (
    <div>
      <Nav />
      <div className="container">
        <h1>Campaigns</h1>
        <div className="card">
          <h3>Create Campaign</h3>
          <input placeholder="Name" value={form.name} onChange={e => setForm({...form, name: e.target.value})} />
          <div className="mt"><input placeholder="Subject ({{first_name}})" value={form.subject_template} onChange={e => setForm({...form, subject_template: e.target.value})} /></div>
          <div className="mt"><textarea placeholder="Body (HTML or text). Links auto-click-tracked, pixel auto-added, unsubscribe auto-added" rows={8} value={form.body_template} onChange={e => setForm({...form, body_template: e.target.value})} /></div>
          <div className="mt"><input placeholder="From Name" value={form.from_name} onChange={e => setForm({...form, from_name: e.target.value})} /></div>
          <div className="mt">
            <select value={form.mailbox_id} onChange={e => setForm({...form, mailbox_id: e.target.value})}>
              <option value="">Any active mailbox</option>
              {mdata?.items?.map((m: any) => <option key={m.id} value={m.id}>{m.email}</option>)}
            </select>
          </div>
          <div className="mt grid">
            <input placeholder="Daily Limit" value={form.daily_limit} onChange={e => setForm({...form, daily_limit: Number(e.target.value)})} />
            <input placeholder="Throttle Per Hour" value={form.throttle_per_hour} onChange={e => setForm({...form, throttle_per_hour: Number(e.target.value)})} />
          </div>
          <div className="mt"><button onClick={create}>Create</button></div>
        </div>
        <div className="card">
          <table>
            <thead><tr><th>Name</th><th>Status</th><th>Daily Limit</th><th>Actions</th></tr></thead>
            <tbody>
              {data?.items?.map((c: any) => (
                <tr key={c.id}>
                  <td>{c.name}</td>
                  <td>{c.status}</td>
                  <td>{c.daily_limit}</td>
                  <td className="flex">
                    <button className="secondary" onClick={() => populate(c.id)}>Populate with leads</button>
                    <button className="secondary" onClick={() => run(c.id)}>Run (via Actions)</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
