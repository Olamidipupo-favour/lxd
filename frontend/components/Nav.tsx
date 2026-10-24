import Link from 'next/link'

export default function Nav() {
  return (
    <nav className="nav">
      <Link href="/">Dashboard</Link>
      <Link href="/mailboxes">Mailboxes</Link>
      <Link href="/leads">Leads</Link>
      <Link href="/campaigns">Campaigns</Link>
      <Link href="/settings">Settings</Link>
    </nav>
  )
}
