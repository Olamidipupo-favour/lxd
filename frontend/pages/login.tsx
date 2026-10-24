import { useState } from 'react'
import { login } from '../lib/api'
import { useRouter } from 'next/router'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const router = useRouter()

  async function submit(e: any) {
    e.preventDefault()
    try {
      await login(email, password)
      router.push('/')
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'Login failed')
    }
  }

  return (
    <div className="container">
      <div className="card" style={{ maxWidth: 400, margin: '80px auto' }}>
        <h2>Admin Login</h2>
        <form onSubmit={submit}>
          <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
          <div className="mt">
            <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
          </div>
          {err && <p style={{ color: '#f87171' }}>{err}</p>}
          <div className="mt">
            <button type="submit">Login</button>
          </div>
        </form>
      </div>
    </div>
  )
}
