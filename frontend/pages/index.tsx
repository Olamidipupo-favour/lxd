import useSWR from 'swr'
import api from '../lib/api'
import Nav from '../components/Nav'
import Tooltip from '../components/Tooltip'

const fetcher = (url: string) => api.get(url).then(r => r.data)

export default function Dashboard() {
  const { data } = useSWR('/stats/overview', fetcher)

  return (
    <div>
      <Nav />
      <div className="p-6">
        <h1 className="text-2xl mb-4">Dashboard</h1>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Tooltip text="Total emails sent across all campaigns"><div className="card"><div className="text-sm text-gray-400">Sent</div><h2 className="text-2xl">{data?.sent || 0}</h2></div></Tooltip>
          <Tooltip text="Email opens tracked (may be unreliable due to privacy features)"><div className="card"><div className="text-sm text-gray-400">Opens (best-effort)</div><h2 className="text-2xl">{data?.opens || 0}</h2></div></Tooltip>
          <Tooltip text="Clicks on tracked links - most reliable engagement metric"><div className="card"><div className="text-sm text-gray-400">Clicks (reliable)</div><h2 className="text-2xl">{data?.clicks || 0}</h2></div></Tooltip>
          <Tooltip text="Replies received"><div className="card"><div className="text-sm text-gray-400">Replies</div><h2 className="text-2xl">{data?.replies || 0}</h2></div></Tooltip>
          <Tooltip text="People who unsubscribed"><div className="card"><div className="text-sm text-gray-400">Unsubscribes</div><h2 className="text-2xl">{data?.unsubs || 0}</h2></div></Tooltip>
          <Tooltip text="Total leads in your database"><div className="card"><div className="text-sm text-gray-400">Leads</div><h2 className="text-2xl">{data?.leads || 0}</h2></div></Tooltip>
          <Tooltip text="Total campaigns created"><div className="card"><div className="text-sm text-gray-400">Campaigns</div><h2 className="text-2xl">{data?.campaigns || 0}</h2></div></Tooltip>
          <Tooltip text="Mailboxes currently active and able to send"><div className="card"><div className="text-sm text-gray-400">Active Mailboxes</div><h2 className="text-2xl">{data?.active_mailboxes || 0}</h2></div></Tooltip>
        </div>
        <div className="card mt-4">
          <h3 className="mb-2">Quick Tips</h3>
          <ul className="text-sm text-gray-400 space-y-1">
            <li>• Opens are unreliable due to Apple Mail privacy features - focus on clicks and replies</li>
            <li>• Always add a few mailboxes and use "Any active mailbox" for rotation</li>
            <li>• Test your SMTP settings before running campaigns</li>
            <li>• Keep your daily limits reasonable to avoid spam flags</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
