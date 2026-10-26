import { useState } from 'react'
import { login } from '../lib/api'
import { useRouter } from 'next/router'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  async function submit(e: any) {
    e.preventDefault()
    setErr('')
    setLoading(true)
    try {
      await login(email, password)
      router.push('/')
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="card w-96">
        <h2 className="text-xl mb-4">Admin Login</h2>
        <form onSubmit={submit}>
          <input className="input mb-2 w-full" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
          <input className="input mb-2 w-full" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
          {err && <p className="text-red-400 text-sm mb-2">{err}</p>}
          <button className="btn w-full" type="submit" disabled={loading}>{loading ? 'Logging in...' : 'Login'}</button>
        </form>
      </div>
    </div>
  )
}
