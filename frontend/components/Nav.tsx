import Link from 'next/link'
import Tooltip from './Tooltip'

export default function Nav() {
  return (
    <nav className="nav">
      <Tooltip text="Overview of your campaigns and performance"><Link href="/">Dashboard</Link></Tooltip>
      <Tooltip text="Manage your sending email accounts"><Link href="/mailboxes">Mailboxes</Link></Tooltip>
      <Tooltip text="Import and manage your contact list"><Link href="/leads">Leads</Link></Tooltip>
      <Tooltip text="Create and run email campaigns"><Link href="/campaigns">Campaigns</Link></Tooltip>
      <Tooltip text="Manage users and team access"><Link href="/users">Users</Link></Tooltip>
      <Tooltip text="System settings"><Link href="/settings">Settings</Link></Tooltip>
    </nav>
  )
}
