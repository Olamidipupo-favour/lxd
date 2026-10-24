import useSWR from 'swr'
import { api } from '../lib/api'
import Nav from '../components/Nav'

const fetcher = (url: string) => api.get(url).then(r => r.data)

export default function Dashboard() {
  const { data } = useSWR('/stats/overview', fetcher)

  return (
    <div>
      <Nav />
      <div className="container">
        <h1>Dashboard</h1>
        <div className="grid">
          <div className="stat"><div>Sent</div><h2>{data?.sent || 0}</h2></div>
          <div className="stat"><div>Opens (best-effort)</div><h2>{data?.opens || 0}</h2></div>
          <div className="stat"><div>Clicks (source of truth)</div><h2>{data?.clicks || 0}</h2></div>
          <div className="stat"><div>Replies</div><h2>{data?.replies || 0}</h2></div>
          <div className="stat"><div>Unsubscribes</div><h2>{data?.unsubs || 0}</h2></div>
          <div className="stat"><div>Leads</div><h2>{data?.leads || 0}</h2></div>
          <div className="stat"><div>Campaigns</div><h2>{data?.campaigns || 0}</h2></div>
          <div className="stat"><div>Active Mailboxes</div><h2>{data?.active_mailboxes || 0}</h2></div>
        </div>
        <div className="card mt">
          <h3>Note</h3>
          <p>Opens are increasingly unreliable due to Apple Mail privacy features. Treat clicks and replies as the real signals.</p>
        </div>
      </div>
    </div>
  )
}
