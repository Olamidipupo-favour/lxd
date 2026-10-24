import { useEffect } from 'react'
import { useRouter } from 'next/router'
import type { AppProps } from 'next/app'
import '../styles/globals.css'
import { api } from '../lib/api'

export default function App({ Component, pageProps }: AppProps) {
  const router = useRouter()

  useEffect(() => {
    if (router.pathname === '/login' || router.pathname === '/settings') return
    api.get('/auth/me')
      .then(() => {})
      .catch(() => {
        router.push('/login')
      })
  }, [router.pathname])

  return <Component {...pageProps} />
}
