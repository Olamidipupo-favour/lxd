import { useState } from 'react'
import useSWR from 'swr'
import { api } from '../lib/api'
import Nav from '../components/Nav'
import Modal from '../components/Modal'
import Tooltip from '../components/Tooltip'

const fetcher = (url: string) => api.get(url).then(r => r.data)

export default function Users() {
  const { data, mutate } = useSWR('/auth/users', fetcher)
  const [showAdd, setShowAdd] = useState(false)
  const [showEdit, setShowEdit] = useState(false)
  const [showReset, setShowReset] = useState(false)
  const [selected, setSelected] = useState<any>(null)
  const [form, setForm] = useState({ email: '', password: '', first_name: '', last_name: '', role: 'user' })
  const [newPass, setNewPass] = useState('')
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState('')

  async function addUser() {
    setLoading(true)
    setMsg('')
    try {
      await api.post('/auth/users', form)
      setShowAdd(false)
      setForm({ email: '', password: '', first_name: '', last_name: '', role: 'user' })
      mutate()
      setMsg('User created successfully')
    } catch (e: any) {
      setMsg(e.response?.data?.detail || 'Error')
    } finally {
      setLoading(false)
    }
  }

  async function updateUser() {
    if (!selected) return
    setLoading(true)
    try {
      await api.put(`/auth/users/${selected.id}`, { first_name: selected.first_name, last_name: selected.last_name, role: selected.role, is_active: selected.is_active })
      setShowEdit(false)
      mutate()
    } finally {
      setLoading(false)
    }
  }

  async function resetPassword() {
    if (!selected) return
    setLoading(true)
    try {
      await api.put(`/auth/users/${selected.id}`, { password: newPass })
      setShowReset(false)
      setNewPass('')
      alert('Password reset successfully')
    } finally {
      setLoading(false)
    }
  }

  async function deleteUser(id: string) {
    if (!confirm('Delete this user?')) return
    setLoading(true)
    try {
      await api.delete(`/auth/users/${id}`)
      mutate()
    } finally {
      setLoading(false)
    }
  }

  const users = data?.users || []

  return (
    <div>
      <Nav />
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl">User Management</h1>
          <Tooltip text="Add a new team member"><button className="btn" onClick={() => setShowAdd(true)}>+ Add User</button></Tooltip>
        </div>
        <div className="card">
          <table className="w-full text-sm">
            <thead><tr className="text-left"><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Last Login</th><th>Actions</th></tr></thead>
            <tbody>
              {users.map((u: any) => (
                <tr key={u.id} className="border-t border-gray-800">
                  <td className="py-2">{[u.first_name, u.last_name].filter(Boolean).join(' ') || '-'}</td>
                  <td>{u.email}</td>
                  <td><span className="px-2 py-1 rounded bg-gray-700 text-xs">{u.role}</span></td>
                  <td>{u.is_active ? <span className="text-green-400">Active</span> : <span className="text-red-400">Inactive</span>}</td>
                  <td>{u.last_login_at ? new Date(u.last_login_at).toLocaleDateString() : 'Never'}</td>
                  <td className="flex gap-1">
                    <Tooltip text="Edit user details"><button className="btn" onClick={() => { setSelected(u); setShowEdit(true) }}>Edit</button></Tooltip>
                    <Tooltip text="Reset password"><button className="btn" onClick={() => { setSelected(u); setShowReset(true) }}>Reset Password</button></Tooltip>
                    <Tooltip text="Remove user"><button className="btn" onClick={() => deleteUser(u.id)}>Delete</button></Tooltip>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Modal open={showAdd} onClose={() => setShowAdd(false)} title="Add New User">
        <div className="space-y-2">
          <input className="input w-full" placeholder="First Name" value={form.first_name} onChange={e => setForm({...form, first_name: e.target.value})} />
          <input className="input w-full" placeholder="Last Name" value={form.last_name} onChange={e => setForm({...form, last_name: e.target.value})} />
          <input className="input w-full" placeholder="Email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} />
          <input className="input w-full" type="password" placeholder="Password" value={form.password} onChange={e => setForm({...form, password: e.target.value})} />
          <select className="input w-full" value={form.role} onChange={e => setForm({...form, role: e.target.value})}>
            <option value="user">User</option>
            <option value="admin">Admin</option>
            <option value="viewer">Viewer</option>
          </select>
          {msg && <div className="text-sm text-red-400">{msg}</div>}
          <button className="btn w-full" onClick={addUser} disabled={loading}>{loading ? 'Creating...' : 'Create User'}</button>
        </div>
      </Modal>

      <Modal open={showEdit} onClose={() => setShowEdit(false)} title="Edit User">
        {selected && (
          <div className="space-y-2">
            <input className="input w-full" placeholder="First Name" value={selected.first_name || ''} onChange={e => setSelected({...selected, first_name: e.target.value})} />
            <input className="input w-full" placeholder="Last Name" value={selected.last_name || ''} onChange={e => setSelected({...selected, last_name: e.target.value})} />
            <select className="input w-full" value={selected.role} onChange={e => setSelected({...selected, role: e.target.value})}>
              <option value="user">User</option>
              <option value="admin">Admin</option>
              <option value="viewer">Viewer</option>
            </select>
            <label className="flex items-center gap-2"><input type="checkbox" checked={selected.is_active} onChange={e => setSelected({...selected, is_active: e.target.checked})} /> Active</label>
            <button className="btn w-full" onClick={updateUser} disabled={loading}>{loading ? 'Saving...' : 'Save Changes'}</button>
          </div>
        )}
      </Modal>

      <Modal open={showReset} onClose={() => setShowReset(false)} title="Reset Password">
        {selected && (
          <div className="space-y-2">
            <p className="text-sm text-gray-400">Reset password for {selected.email}</p>
            <input className="input w-full" type="password" placeholder="New Password" value={newPass} onChange={e => setNewPass(e.target.value)} />
            <button className="btn w-full" onClick={resetPassword} disabled={loading || !newPass}>{loading ? 'Resetting...' : 'Reset Password'}</button>
          </div>
        )}
      </Modal>
    </div>
  )
}
