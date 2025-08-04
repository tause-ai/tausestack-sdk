'use client'

import { useAuth } from '../../contexts/AuthContext'
import { useRouter, usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import LoginForm from './LoginForm'
import Navigation from './Navigation'

export default function AuthWrapper({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()
  const [isClient, setIsClient] = useState(false)
  
  // Fix hydration error: wait for client-side mounting
  useEffect(() => {
    setIsClient(true)
  }, [])

  useEffect(() => {
    if (!loading && isClient) {
      // Si el usuario está autenticado y está en la raíz, redirigir al admin
      if (user && pathname === '/') {
        router.push('/admin')
      }
      
      // Si el usuario NO está autenticado y está en una ruta protegida, redirigir al login
      if (!user && (pathname.startsWith('/admin') || pathname.startsWith('/mcp'))) {
        router.push('/')
      }
    }
  }, [user, loading, pathname, router, isClient])

  // Show loading during hydration and auth loading
  if (!isClient || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  // Si no está autenticado, mostrar login solo en rutas públicas
  if (!user && !pathname.startsWith('/admin')) {
    return <LoginForm />
  }

  // Si está autenticado y en una ruta de admin o mcp, mostrar la interfaz completa
  if (user && (pathname.startsWith('/admin') || pathname.startsWith('/mcp'))) {
    return (
      <div className="flex h-screen bg-gray-100">
        <Navigation />
        <main className="flex-1 p-6 bg-gray-50 min-h-screen">
          {children}
        </main>
      </div>
    )
  }

  // Para cualquier otra situación, mostrar contenido básico
  return <div className="min-h-screen bg-gray-50">{children}</div>
} 