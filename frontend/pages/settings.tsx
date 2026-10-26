import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import { api, setup } from '../lib/api'
import Nav from '../components/Nav'

export default function Settings() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [msg, setMsg] = useState('')
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<any>(null)

  useEffect(() => {
    api.get('/auth/setup-status').then(r => {
      setStatus(r.data)
      if (r.data.has_admin) router.push('/login')
    }).catch(() => {})
  }, [])

  async function doSetup() {
    setMsg('')
    setLoading(true)
    try {
      await setup(email, password)
      setMsg('Admin created. Redirecting to login...')
      setTimeout(() => router.push('/login'), 1000)
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'Error')
    } finally {
      setLoading(false)
    }
  }

  if (status?.has_admin) return <div className="p-6">Redirecting...</div>
  return (
    <div>
      <Nav />
      <div className="p-6">
        <div className="card max-w-md">
          <h3 className="text-xl mb-2">First-time Admin Setup</h3>
          <p className="text-sm text-gray-400 mb-4">If no admin exists, create one here.</p>
          <input className="input w-full mb-2" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
          <input className="input w-full mb-2" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
          <button className="btn" onClick={doSetup} disabled={loading}>{loading ? 'Creating...' : 'Create Admin'}</button>
          {msg && <p className="text-sm mt-2">{msg}</p>}
        </div>
      </div>
    </div>
  )
}
