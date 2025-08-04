'use client'

import { useAuth } from '../contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function HomePage() {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    // Si ya está autenticado, redirigir automáticamente al dashboard
    if (!loading && user) {
      router.push('/dashboard')
    }
  }, [user, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  // Si no está autenticado, AuthWrapper ya mostrará LoginForm
  // Esta página es para casos edge o contenido adicional
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-blue-50 to-cyan-50">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-6">
            TauseStack Admin
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Plataforma de gestión multi-tenant con servicios AI-powered
          </p>
          
          <div className="grid md:grid-cols-3 gap-8 mt-12">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-indigo-600 text-3xl mb-4">🏢</div>
              <h3 className="text-lg font-semibold mb-2">Multi-Tenant</h3>
              <p className="text-gray-600">Gestión avanzada de múltiples inquilinos con aislamiento completo</p>
      </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-indigo-600 text-3xl mb-4">🤖</div>
              <h3 className="text-lg font-semibold mb-2">AI-Powered</h3>
              <p className="text-gray-600">Servicios inteligentes con generación automática de código</p>
        </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-indigo-600 text-3xl mb-4">📊</div>
              <h3 className="text-lg font-semibold mb-2">Analytics</h3>
              <p className="text-gray-600">Métricas en tiempo real y reportes avanzados</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
