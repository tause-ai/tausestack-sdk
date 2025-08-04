'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Users, 
  Building, 
  Plus,
  Search,
  Settings,
  Activity,
  Calendar,
  DollarSign,
  MoreVertical
} from 'lucide-react'

interface Tenant {
  id: string
  name: string
  domain: string
  plan: 'free' | 'basic' | 'premium' | 'enterprise'
  status: 'active' | 'inactive' | 'suspended'
  users_count: number
  api_calls_month: number
  storage_gb: number
  created_at: string
  last_activity: string
  revenue_month: number
  admin_email: string
}

export default function TenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedPlan, setSelectedPlan] = useState('all')

  useEffect(() => {
    // Datos de ejemplo
    const mockTenants: Tenant[] = [
      {
        id: 'tenant_1',
        name: 'Empresa ABC',
        domain: 'abc.tausestack.dev',
        plan: 'enterprise',
        status: 'active',
        users_count: 45,
        api_calls_month: 125000,
        storage_gb: 15.2,
        created_at: '2024-01-15',
        last_activity: '2024-01-20',
        revenue_month: 299,
        admin_email: 'admin@empresaabc.com'
      },
      {
        id: 'tenant_2',
        name: 'StartupXYZ',
        domain: 'xyz.tausestack.dev',
        plan: 'premium',
        status: 'active',
        users_count: 12,
        api_calls_month: 45000,
        storage_gb: 5.8,
        created_at: '2024-01-10',
        last_activity: '2024-01-19',
        revenue_month: 99,
        admin_email: 'founder@startupxyz.com'
      },
      {
        id: 'tenant_3',
        name: 'DevTeam Pro',
        domain: 'devteam.tausestack.dev',
        plan: 'basic',
        status: 'active',
        users_count: 8,
        api_calls_month: 15000,
        storage_gb: 2.1,
        created_at: '2024-01-08',
        last_activity: '2024-01-18',
        revenue_month: 29,
        admin_email: 'dev@devteampro.com'
      },
      {
        id: 'tenant_4',
        name: 'Testing Inc',
        domain: 'testing.tausestack.dev',
        plan: 'free',
        status: 'inactive',
        users_count: 3,
        api_calls_month: 2500,
        storage_gb: 0.5,
        created_at: '2024-01-05',
        last_activity: '2024-01-15',
        revenue_month: 0,
        admin_email: 'test@testing.com'
      }
    ]
    
    setTimeout(() => {
      setTenants(mockTenants)
      setLoading(false)
    }, 1000)
  }, [])

  const plans = [
    { value: 'all', label: 'Todos los planes' },
    { value: 'free', label: 'Free' },
    { value: 'basic', label: 'Basic' },
    { value: 'premium', label: 'Premium' },
    { value: 'enterprise', label: 'Enterprise' }
  ]

  const filteredTenants = tenants.filter(tenant => {
    const matchesSearch = tenant.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         tenant.domain.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         tenant.admin_email.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesPlan = selectedPlan === 'all' || tenant.plan === selectedPlan
    return matchesSearch && matchesPlan
  })

  const getPlanColor = (plan: string) => {
    const colors = {
      free: 'bg-gray-100 text-gray-800',
      basic: 'bg-blue-100 text-blue-800',
      premium: 'bg-purple-100 text-purple-800',
      enterprise: 'bg-yellow-100 text-yellow-800'
    }
    return colors[plan as keyof typeof colors] || 'bg-gray-100 text-gray-800'
  }

  const getStatusColor = (status: string) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      suspended: 'bg-red-100 text-red-800'
    }
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Tenants</h1>
            <p className="text-gray-600 mt-1">Gestión de inquilinos del sistema multi-tenant</p>
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Nuevo Tenant
          </Button>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Building className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">{tenants.length}</p>
                  <p className="text-sm text-gray-600">Total Tenants</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Activity className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">
                    {tenants.filter(t => t.status === 'active').length}
                  </p>
                  <p className="text-sm text-gray-600">Activos</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Users className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">
                    {tenants.reduce((acc, t) => acc + t.users_count, 0)}
                  </p>
                  <p className="text-sm text-gray-600">Total Usuarios</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <DollarSign className="h-5 w-5 text-yellow-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">
                    ${tenants.reduce((acc, t) => acc + t.revenue_month, 0)}
                  </p>
                  <p className="text-sm text-gray-600">Revenue MTD</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="p-4">
            <div className="flex gap-4 items-center">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Buscar tenants..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              <select
                value={selectedPlan}
                onChange={(e) => setSelectedPlan(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {plans.map(plan => (
                  <option key={plan.value} value={plan.value}>{plan.label}</option>
                ))}
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Tenants List */}
        <Card>
          <CardHeader>
            <CardTitle>Lista de Tenants</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {filteredTenants.map(tenant => (
                <div key={tenant.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-gray-900">{tenant.name}</h3>
                        <Badge className={getPlanColor(tenant.plan)}>
                          {tenant.plan}
                        </Badge>
                        <Badge className={getStatusColor(tenant.status)}>
                          {tenant.status}
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <p className="text-gray-500">Dominio</p>
                          <p className="font-medium">{tenant.domain}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Usuarios</p>
                          <p className="font-medium">{tenant.users_count}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">API Calls/mes</p>
                          <p className="font-medium">{tenant.api_calls_month.toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Storage</p>
                          <p className="font-medium">{tenant.storage_gb} GB</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                        <span>Admin: {tenant.admin_email}</span>
                        <span>Creado: {tenant.created_at}</span>
                        <span>Última actividad: {tenant.last_activity}</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold text-green-600">
                        ${tenant.revenue_month}/mes
                      </span>
                      <Button variant="outline" size="sm">
                        <Settings className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {filteredTenants.length === 0 && (
              <div className="text-center py-12">
                <Building className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No se encontraron tenants</h3>
                <p className="text-gray-600">Intenta ajustar los filtros de búsqueda</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 