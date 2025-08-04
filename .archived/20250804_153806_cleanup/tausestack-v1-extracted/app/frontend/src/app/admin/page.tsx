'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Users, 
  Activity, 
  DollarSign, 
  Zap, 
  TrendingUp, 
  Globe, 
  AlertTriangle,
  CheckCircle,
  Clock,
  ArrowUpRight,
  Bell,
  RefreshCw
} from 'lucide-react'

interface DashboardMetrics {
  apiCallsToday: number
  apiCallsGrowth: number
  activeTenants: number
  newTenantsWeek: number
  revenueMTD: number
  revenueGrowth: number
  uptime: number
  incidents: number
  requestsPerSecond: number
  avgResponseTime: number
  errorRate: number
  timestamp: number
}

interface TopEndpoint {
  path: string
  calls: number
  icon: string
}

interface TopTenant {
  name: string
  plan: string
  calls: number
  revenue: number
  badge: string
}

interface RecentActivity {
  type: 'new_tenant' | 'alert' | 'plugin' | 'maintenance' | 'support' | 'payment' | 'upgrade' | 'integration' | 'backup' | 'security'
  message: string
  time: string
  icon: string
}

export default function TauseStackConsole() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [topEndpoints, setTopEndpoints] = useState<TopEndpoint[]>([])
  const [topTenants, setTopTenants] = useState<TopTenant[]>([])
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  const fetchDashboardData = async () => {
    try {
      const baseUrl = process.env.NODE_ENV === 'development' 
        ? 'http://localhost:8001' 
        : 'https://api.tausestack.dev'

      // Hacer todas las peticiones en paralelo
      const [metricsRes, endpointsRes, tenantsRes, activityRes] = await Promise.all([
        fetch(`${baseUrl}/admin/dashboard/metrics`),
        fetch(`${baseUrl}/admin/dashboard/top-endpoints`),
        fetch(`${baseUrl}/admin/dashboard/top-tenants`),
        fetch(`${baseUrl}/admin/dashboard/recent-activity`)
      ])

      if (metricsRes.ok) {
        const metricsData = await metricsRes.json()
        setMetrics(metricsData)
      }

      if (endpointsRes.ok) {
        const endpointsData = await endpointsRes.json()
        setTopEndpoints(endpointsData)
      }

      if (tenantsRes.ok) {
        const tenantsData = await tenantsRes.json()
        setTopTenants(tenantsData)
      }

      if (activityRes.ok) {
        const activityData = await activityRes.json()
        setRecentActivity(activityData)
      }

      setLastUpdate(new Date())
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  // Cargar datos iniciales
  useEffect(() => {
    fetchDashboardData()
  }, [])

  // Auto-refresh cada 30 segundos
  useEffect(() => {
    const interval = setInterval(() => {
      fetchDashboardData()
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  const handleRefresh = () => {
    setRefreshing(true)
    fetchDashboardData()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
      </div>
    )
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(0)}K`
    return num.toString()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Welcome back, Admin! 👋</h1>
            <p className="text-gray-600 mt-1">TauseStack Console Dashboard</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-xs text-gray-500">
              Última actualización: {lastUpdate.toLocaleTimeString()}
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Actualizando...' : 'Actualizar'}
            </Button>
            <Button variant="outline" size="sm">
              <Bell className="h-4 w-4 mr-2" />
              3 new alerts
            </Button>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* System Overview */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-medium">System Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Activity className="h-5 w-5 text-blue-600" />
                  </div>
                  <span className="text-sm font-medium text-gray-600">API Calls Today</span>
                </div>
                <div className="space-y-1">
                  <p className="text-2xl font-bold text-gray-900">
                    {metrics ? formatNumber(metrics.apiCallsToday) : '0'}
                  </p>
                  <p className="text-sm text-green-600 flex items-center gap-1">
                    <ArrowUpRight className="h-3 w-3" />
                    +{metrics?.apiCallsGrowth || 0}% vs yesterday
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Users className="h-5 w-5 text-green-600" />
                  </div>
                  <span className="text-sm font-medium text-gray-600">Active Tenants</span>
                </div>
                <div className="space-y-1">
                  <p className="text-2xl font-bold text-gray-900">
                    {metrics?.activeTenants || 0}
                  </p>
                  <p className="text-sm text-green-600">
                    +{metrics?.newTenantsWeek || 0} new this week
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-yellow-100 rounded-lg">
                    <DollarSign className="h-5 w-5 text-yellow-600" />
                  </div>
                  <span className="text-sm font-medium text-gray-600">Revenue MTD</span>
                </div>
                <div className="space-y-1">
                  <p className="text-2xl font-bold text-gray-900">
                    ${metrics ? formatNumber(metrics.revenueMTD) : '0'}
                  </p>
                  <p className="text-sm text-green-600 flex items-center gap-1">
                    <ArrowUpRight className="h-3 w-3" />
                    +{metrics?.revenueGrowth || 0}% vs last month
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Zap className="h-5 w-5 text-purple-600" />
                  </div>
                  <span className="text-sm font-medium text-gray-600">Uptime</span>
                </div>
                <div className="space-y-1">
                  <p className="text-2xl font-bold text-gray-900">
                    {metrics?.uptime || 0}%
                  </p>
                  <p className="text-sm text-gray-500">
                    {metrics?.incidents || 0} incidents
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Real-time Metrics & Top Endpoints */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg font-medium flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Real-time Metrics
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 gap-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">Requests/sec</span>
                  <span className="text-lg font-bold text-blue-600">
                    {metrics?.requestsPerSecond || 0}
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">Avg Response</span>
                  <span className="text-lg font-bold text-green-600">
                    {metrics?.avgResponseTime || 0}ms
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">Error Rate</span>
                  <span className="text-lg font-bold text-orange-600">
                    {metrics?.errorRate || 0}%
                  </span>
                </div>
              </div>
              
              <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-green-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Globe className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium">Global Requests</span>
                </div>
                <div className="text-xs text-gray-600">Interactive world map would go here</div>
                <div className="mt-2 h-16 bg-gradient-to-r from-blue-200 to-green-200 rounded opacity-50 flex items-center justify-center">
                  <span className="text-xs text-gray-700">🌍 Live Global Activity</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg font-medium">Top API Endpoints</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {topEndpoints.map((endpoint, index) => (
                  <div key={endpoint.path} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg transition-colors">
                    <div className="flex items-center gap-3">
                      <span className="text-lg">{endpoint.icon}</span>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{endpoint.path}</p>
                        <p className="text-xs text-gray-500">{formatNumber(endpoint.calls)} calls</p>
                      </div>
                    </div>
                    <Badge variant="secondary" className="text-xs">
                      #{index + 1}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Top Tenants & Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg font-medium">Top Consuming Tenants</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topTenants.map((tenant, index) => (
                  <div key={tenant.name} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:shadow-sm transition-shadow">
                    <div className="flex items-center gap-3">
                      <span className="text-xl">{tenant.badge}</span>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-gray-900">{tenant.name}</p>
                          <Badge variant="outline" className="text-xs">
                            {tenant.plan}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600">
                          {formatNumber(tenant.calls)} calls • ${formatNumber(tenant.revenue)}/month
                        </p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm">
                      View Details
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg font-medium">Recent Activity</CardTitle>
                <Button variant="ghost" size="sm" className="text-sm text-blue-600">
                  View all →
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentActivity.map((activity, index) => (
                  <div key={index} className="flex items-start gap-3 p-3 hover:bg-gray-50 rounded-lg transition-colors">
                    <span className="text-lg">{activity.icon}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900">{activity.message}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Clock className="h-3 w-3 text-gray-400" />
                        <span className="text-xs text-gray-500">{activity.time}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
} 