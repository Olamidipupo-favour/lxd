import { useState } from 'react'
import useSWR from 'swr'
import { api } from '../lib/api'
import Nav from '../components/Nav'

const fetcher = (url: string) => api.get(url).then(r => r.data)

export default function Mailboxes() {
  const { data, mutate } = useSWR('/mailboxes/', fetcher)
  const [form, setForm] = useState({ email: '', smtp_host: 'smtp.gmail.com', smtp_port: 587, username: '', password: '', daily_cap: 5, status: 'warming' })

  async function add() {
    await api.post('/mailboxes/', form)
    setForm({ email: '', smtp_host: 'smtp.gmail.com', smtp_port: 587, username: '', password: '', daily_cap: 5, status: 'warming' })
    mutate()
  }

  async function toggle(m: any) {
    const status = m.status === 'active' ? 'paused' : 'active'
    await api.put(`/mailboxes/${m.id}`, { status })
    mutate()
  }

  async function del(m: any) {
    if (!confirm('Delete mailbox?')) return
    await api.delete(`/mailboxes/${m.id}`)
    mutate()
  }

  return (
    <div>
      <Nav />
      <div className="container">
        <h1>Mailboxes</h1>
        <div className="card">
          <h3>Add Mailbox (SMTP)</h3>
          <div className="grid">
            <input placeholder="Email (e.g. cold@domain.com)" value={form.email} onChange={e => setForm({...form, email: e.target.value})} />
            <input placeholder="SMTP Host" value={form.smtp_host} onChange={e => setForm({...form, smtp_host: e.target.value})} />
            <input placeholder="SMTP Port" value={form.smtp_port} onChange={e => setForm({...form, smtp_port: Number(e.target.value)})} />
            <input placeholder="Username" value={form.username} onChange={e => setForm({...form, username: e.target.value})} />
            <input placeholder="Password/App Password" type="password" value={form.password} onChange={e => setForm({...form, password: e.target.value})} />
            <input placeholder="Daily Cap" value={form.daily_cap} onChange={e => setForm({...form, daily_cap: Number(e.target.value)})} />
            <select value={form.status} onChange={e => setForm({...form, status: e.target.value})}>
              <option value="warming">warming</option>
              <option value="active">active</option>
              <option value="paused">paused</option>
            </select>
          </div>
          <div className="mt"><button onClick={add}>Add Mailbox</button></div>
        </div>
        <div className="card">
          <table>
            <thead><tr><th>Email</th><th>Domain</th><th>Host:Port</th><th>Cap</th><th>Sent Today</th><th>Status</th><th>Errors</th><th>Actions</th></tr></thead>
            <tbody>
              {data?.items?.map((m: any) => (
                <tr key={m.id}>
                  <td>{m.email}</td>
                  <td>{m.domain}</td>
                  <td>{m.smtp_host}:{m.smtp_port}</td>
                  <td>{m.daily_cap}</td>
                  <td>{m.emails_sent_today}</td>
                  <td>{m.status}</td>
                  <td>{m.consecutive_errors}</td>
                  <td className="flex">
                    <button className="secondary" onClick={() => toggle(m)}>{m.status === 'active' ? 'Pause' : 'Activate'}</button>
                    <button className="secondary" onClick={() => del(m)}>Delete</button>
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
