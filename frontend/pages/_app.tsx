import { useEffect } from 'react'
import { useRouter } from 'next/router'
import type { AppProps } from 'next/app'
import '../styles/globals.css'
import { api } from '../lib/api'

export default function App({ Component, pageProps }: AppProps) {
  const router = useRouter()

  useEffect(() => {
    if (router.pathname === '/login') return

    async function check() {
      if (router.pathname === '/settings') {
        try {
          const { data } = await api.get('/auth/setup-status')
          if (!data.admin_exists) return
        } catch {
          router.push('/login')
          return
        }
      }
      try {
        await api.get('/auth/me')
      } catch {
        router.push('/login')
      }
    }

    check()
  }, [router.pathname])

  return <Component {...pageProps} />
}
