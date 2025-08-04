'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Activity, 
  TrendingUp, 
  Clock, 
  Zap,
  Server,
  Database,
  Users,
  Globe,
  AlertTriangle,
  CheckCircle,
  RefreshCw
} from 'lucide-react'

interface MetricData {
  label: string
  value: number
  change: number
  unit: string
}

interface SystemHealth {
  api_gateway: 'healthy' | 'warning' | 'critical'
  database: 'healthy' | 'warning' | 'critical'
  storage: 'healthy' | 'warning' | 'critical'
  cache: 'healthy' | 'warning' | 'critical'
}

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<MetricData[]>([])
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  useEffect(() => {
    fetchMetrics()
  }, [])

  const fetchMetrics = async () => {
    setRefreshing(true)
    
    // Simular datos de métricas
    const mockMetrics: MetricData[] = [
      { label: 'API Calls', value: 1250000, change: 12.5, unit: '/day' },
      { label: 'Response Time', value: 145, change: -8.2, unit: 'ms' },
      { label: 'Error Rate', value: 0.05, change: -15.3, unit: '%' },
      { label: 'Throughput', value: 850, change: 18.7, unit: 'req/s' },
      { label: 'Active Users', value: 15420, change: 7.3, unit: '' },
      { label: 'Storage Used', value: 245.8, change: 5.4, unit: 'GB' },
      { label: 'Database Queries', value: 89200, change: 22.1, unit: '/hour' },
      { label: 'Cache Hit Rate', value: 94.2, change: 2.8, unit: '%' }
    ]

    const mockSystemHealth: SystemHealth = {
      api_gateway: 'healthy',
      database: 'healthy',
      storage: 'warning',
      cache: 'healthy'
    }

    setTimeout(() => {
      setMetrics(mockMetrics)
      setSystemHealth(mockSystemHealth)
      setLoading(false)
      setRefreshing(false)
      setLastUpdate(new Date())
    }, 1000)
  }

  const getHealthColor = (status: string) => {
    const colors = {
      healthy: 'text-green-600 bg-green-100',
      warning: 'text-yellow-600 bg-yellow-100',
      critical: 'text-red-600 bg-red-100'
    }
    return colors[status as keyof typeof colors] || 'text-gray-600 bg-gray-100'
  }

  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4" />
      case 'critical':
        return <AlertTriangle className="h-4 w-4" />
      default:
        return <Clock className="h-4 w-4" />
    }
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
            <h1 className="text-2xl font-semibold text-gray-900">Métricas del Sistema</h1>
            <p className="text-gray-600 mt-1">Monitoreo en tiempo real del rendimiento de TauseStack</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-xs text-gray-500">
              Última actualización: {lastUpdate.toLocaleTimeString()}
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={fetchMetrics}
              disabled={refreshing}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Actualizando...' : 'Actualizar'}
            </Button>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* System Health */}
        <Card>
          <CardHeader>
            <CardTitle>Estado del Sistema</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="flex items-center gap-3 p-3 rounded-lg border">
                <Server className="h-5 w-5 text-blue-600" />
                <div className="flex-1">
                  <p className="text-sm font-medium">API Gateway</p>
                  <div className={`flex items-center gap-1 text-xs ${getHealthColor(systemHealth?.api_gateway || 'healthy')}`}>
                    {getHealthIcon(systemHealth?.api_gateway || 'healthy')}
                    <span className="capitalize">{systemHealth?.api_gateway}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 rounded-lg border">
                <Database className="h-5 w-5 text-green-600" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Database</p>
                  <div className={`flex items-center gap-1 text-xs ${getHealthColor(systemHealth?.database || 'healthy')}`}>
                    {getHealthIcon(systemHealth?.database || 'healthy')}
                    <span className="capitalize">{systemHealth?.database}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 rounded-lg border">
                <Globe className="h-5 w-5 text-purple-600" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Storage</p>
                  <div className={`flex items-center gap-1 text-xs ${getHealthColor(systemHealth?.storage || 'healthy')}`}>
                    {getHealthIcon(systemHealth?.storage || 'healthy')}
                    <span className="capitalize">{systemHealth?.storage}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 rounded-lg border">
                <Zap className="h-5 w-5 text-yellow-600" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Cache</p>
                  <div className={`flex items-center gap-1 text-xs ${getHealthColor(systemHealth?.cache || 'healthy')}`}>
                    {getHealthIcon(systemHealth?.cache || 'healthy')}
                    <span className="capitalize">{systemHealth?.cache}</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {metrics.map((metric, index) => {
            const icons = [Activity, Clock, AlertTriangle, TrendingUp, Users, Database, Server, Zap]
            const Icon = icons[index % icons.length]
            
            return (
              <Card key={metric.label}>
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <Icon className="h-5 w-5 text-blue-600" />
                    </div>
                    <h3 className="font-medium text-gray-900">{metric.label}</h3>
                  </div>
                  
                  <div className="space-y-2">
                    <p className="text-2xl font-bold text-gray-900">
                      {metric.value.toLocaleString()}
                      <span className="text-sm font-normal text-gray-500">{metric.unit}</span>
                    </p>
                    
                    <div className="flex items-center gap-1">
                      <TrendingUp className={`h-3 w-3 ${metric.change >= 0 ? 'text-green-600' : 'text-red-600'}`} />
                      <span className={`text-xs ${metric.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {metric.change >= 0 ? '+' : ''}{metric.change}%
                      </span>
                      <span className="text-xs text-gray-500">vs ayer</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {/* Performance Chart Placeholder */}
        <Card>
          <CardHeader>
            <CardTitle>Rendimiento en Tiempo Real</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
              <div className="text-center">
                <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">Gráfico de rendimiento en tiempo real</p>
                <p className="text-sm text-gray-500 mt-1">
                  Aquí se mostraría un gráfico con métricas de API calls, latencia y errores
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* API Endpoints Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Top Endpoints por Volumen</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { path: '/api/v1/auth/login', calls: 125000, avgTime: 120, status: 'healthy' },
                { path: '/api/v1/tenants', calls: 89000, avgTime: 85, status: 'healthy' },
                { path: '/api/v1/storage/upload', calls: 67000, avgTime: 340, status: 'warning' },
                { path: '/api/v1/ai/generate', calls: 45000, avgTime: 2100, status: 'healthy' },
                { path: '/api/v1/analytics/track', calls: 234000, avgTime: 45, status: 'healthy' }
              ].map((endpoint, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{endpoint.path}</p>
                    <p className="text-sm text-gray-600">{endpoint.calls.toLocaleString()} calls</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">{endpoint.avgTime}ms</p>
                    <Badge 
                      className={`text-xs ${
                        endpoint.status === 'healthy' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {endpoint.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 