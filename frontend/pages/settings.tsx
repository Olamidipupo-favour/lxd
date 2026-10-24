import { useState } from 'react'
import { setup } from '../lib/api'
import Nav from '../components/Nav'

export default function Settings() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [ok, setOk] = useState(false)

  async function doSetup() {
    await setup(email, password)
    setOk(true)
  }

  return (
    <div>
      <Nav />
      <div className="container">
        <h1>Settings</h1>
        <div className="card">
          <h3>First-time Admin Setup</h3>
          <p>If no admin exists, create one here.</p>
          <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
          <div className="mt"><input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} /></div>
          <div className="mt"><button onClick={doSetup}>Create Admin</button></div>
          {ok && <p style={{ color: '#34d399' }}>Admin created. Go to Login.</p>}
        </div>
      </div>
    </div>
  )
}
