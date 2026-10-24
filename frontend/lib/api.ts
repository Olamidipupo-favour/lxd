import axios from 'axios'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API,
  withCredentials: true,
})

export async function login(email: string, password: string) {
  const res = await api.post('/auth/login', { email, password })
  return res.data
}

export async function me() {
  const res = await api.get('/auth/me')
  return res.data
}

export async function setup(email: string, password: string) {
  const res = await api.post('/auth/setup', { email, password })
  return res.data
}
