import { useState } from 'react'
import useSWR from 'swr'
import { api } from '../lib/api'
import Nav from '../components/Nav'

const fetcher = (url: string) => api.get(url).then(r => r.data)

export default function Leads() {
  const { data, mutate } = useSWR('/leads/?limit=200', fetcher)
  const [file, setFile] = useState<File | null>(null)

  async function upload() {
    if (!file) return
    const fd = new FormData()
    fd.append('file', file)
    await api.post('/leads/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    setFile(null)
    mutate()
  }

  return (
    <div>
      <Nav />
      <div className="container">
        <h1>Leads</h1>
        <div className="card">
          <h3>CSV Upload</h3>
          <p>Columns: email, first_name, last_name, company, title, website, phone (extra columns go to custom_fields)</p>
          <input type="file" accept=".csv" onChange={e => setFile(e.target.files?.[0] || null)} />
          <div className="mt"><button onClick={upload}>Upload</button></div>
        </div>
        <div className="card">
          <table>
            <thead><tr><th>Email</th><th>Name</th><th>Company</th><th>Title</th><th>Status</th><th>Source</th></tr></thead>
            <tbody>
              {data?.items?.map((l: any) => (
                <tr key={l.id}>
                  <td>{l.email}</td>
                  <td>{l.first_name} {l.last_name}</td>
                  <td>{l.company}</td>
                  <td>{l.title}</td>
                  <td>{l.status}</td>
                  <td>{l.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
