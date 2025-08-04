'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Plus, 
  Play, 
  Save, 
  Settings, 
  Layers, 
  Code, 
  Globe, 
  Database,
  Zap,
  RefreshCw,
  FolderOpen,
  Trash2,
  Edit,
  Eye,
  Upload,
  Download,
  CheckCircle,
  AlertCircle,
  Clock
} from 'lucide-react'
import { ApiClient } from '@/lib/api'

interface Project {
  id: string
  name: string
  description: string
  type: 'web' | 'api' | 'agent' | 'ecommerce' | 'dashboard'
  status: 'draft' | 'building' | 'ready' | 'deployed' | 'error'
  tenant_id: string
  created_at: string
  updated_at: string
  components: ProjectComponent[]
  config: ProjectConfig
  // Campos adicionales del Builder API
  build_logs?: string[]
  endpoints?: {
    frontend?: string
    api?: string
    admin?: string
    local_path?: string
  }
}

interface ProjectComponent {
  id: string
  type: 'page' | 'component' | 'api' | 'database' | 'service'
  name: string
  config: any
  dependencies: string[]
}

interface ProjectConfig {
  domain?: string
  database_type?: 'supabase' | 'postgres' | 'mysql'
  ai_services?: string[]
  notifications?: boolean
  analytics?: boolean
}

interface BuilderStats {
  total_projects: number
  active_builds: number
  successful_deploys: number
  failed_deploys: number
  templates_used: number
}

export default function BuilderPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [stats, setStats] = useState<BuilderStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [view, setView] = useState<'grid' | 'list'>('grid')
  const [filter, setFilter] = useState<string>('all')
  const [isCreating, setIsCreating] = useState(false)
  const [showNewProjectModal, setShowNewProjectModal] = useState(false)

  // Nuevo proyecto
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    type: 'web' as Project['type'],
    template_id: ''
  })

  // Cargar datos
  useEffect(() => {
    loadBuilderData()
  }, [])

  const loadBuilderData = async () => {
    try {
      setLoading(true)
      
      // Cargar proyectos y stats en paralelo
      const [projectsRes, statsRes] = await Promise.all([
        ApiClient.get('/api/builder/projects'),
        ApiClient.get('/api/builder/stats')
      ])

      if (projectsRes.ok) {
        const projectsData = await projectsRes.json()
        
        // Transformar datos del Builder API al formato esperado por el frontend
        const transformedProjects = projectsData.map((app: any) => ({
          id: app.app_id,
          name: app.app_name,
          description: app.template_id === 'website' ? 'Aplicación web completa con frontend y backend' : 
                      app.template_id === 'advanced-dashboard' ? 'Dashboard avanzado con métricas y reportes' :
                      app.template_id === 'ecommerce-complete' ? 'Tienda online completa con carrito y pagos' :
                      `Aplicación basada en template ${app.template_id}`,
          type: app.template_id === 'website' ? 'web' : 
                app.template_id === 'advanced-dashboard' ? 'dashboard' :
                app.template_id === 'ecommerce-complete' ? 'ecommerce' : 'web',
          status: app.status,
          tenant_id: app.tenant_id,
          created_at: app.created_at,
          updated_at: app.created_at, // Usar created_at como updated_at por ahora
          components: [], // Por ahora empty array
          config: {
            domain: app.endpoints?.frontend || '',
            database_type: 'supabase' as const,
            ai_services: [],
            notifications: true,
            analytics: true
          },
          // Datos adicionales del Builder API
          build_logs: app.build_logs || [],
          endpoints: app.endpoints || {}
        }))
        
        setProjects(transformedProjects)
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json()
        setStats(statsData)
      } else {
        // Calcular stats básicas si no hay endpoint
        const totalProjects = projects.length
        const activeBuilds = projects.filter(p => p.status === 'building').length
        const successfulDeploys = projects.filter(p => p.status === 'deployed').length
        const failedDeploys = projects.filter(p => p.status === 'error').length
        
        setStats({
          total_projects: totalProjects,
          active_builds: activeBuilds,
          successful_deploys: successfulDeploys,
          failed_deploys: failedDeploys,
          templates_used: 0
        })
      }
    } catch (error) {
      console.error('Error loading builder data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateProject = async () => {
    try {
      setIsCreating(true)
      
      // Mapear el tipo de proyecto a template_id
      const templateMapping = {
        'web': 'website',
        'dashboard': 'advanced-dashboard',
        'ecommerce': 'ecommerce-complete',
        'api': 'website',
        'agent': 'website'
      }
      
      const response = await ApiClient.post('/api/builder/projects', {
        template_id: templateMapping[newProject.type as keyof typeof templateMapping] || 'website',
        app_name: newProject.name,
        tenant_id: 'default',
        configuration: {
          description: newProject.description
        }
      })

      if (response.ok) {
        const createdApp = await response.json()
        
        // Transformar la respuesta al formato del frontend
        const transformedProject = {
          id: createdApp.app_id,
          name: createdApp.app_name,
          description: newProject.description,
          type: newProject.type,
          status: createdApp.status,
          tenant_id: createdApp.tenant_id,
          created_at: createdApp.created_at,
          updated_at: createdApp.created_at,
          components: [],
          config: {
            domain: createdApp.endpoints?.frontend || '',
            database_type: 'supabase' as const,
            ai_services: [],
            notifications: true,
            analytics: true
          },
          build_logs: createdApp.build_logs || [],
          endpoints: createdApp.endpoints || {}
        }
        
        setProjects(prev => [...prev, transformedProject])
        setShowNewProjectModal(false)
        setNewProject({ name: '', description: '', type: 'web', template_id: '' })
      }
    } catch (error) {
      console.error('Error creating project:', error)
    } finally {
      setIsCreating(false)
    }
  }

  const handleBuildProject = async (projectId: string) => {
    try {
      const response = await ApiClient.post(`/api/builder/projects/${projectId}/build`)
      
      if (response.ok) {
        // Actualizar estado del proyecto
        setProjects(prev => 
          prev.map(p => 
            p.id === projectId 
              ? { ...p, status: 'building' }
              : p
          )
        )
      }
    } catch (error) {
      console.error('Error building project:', error)
    }
  }

  const handleDeployProject = async (projectId: string) => {
    try {
      const response = await ApiClient.post(`/api/builder/projects/${projectId}/deploy`)
      
      if (response.ok) {
        // Actualizar estado del proyecto
        setProjects(prev => 
          prev.map(p => 
            p.id === projectId 
              ? { ...p, status: 'deployed' }
              : p
          )
        )
      }
    } catch (error) {
      console.error('Error deploying project:', error)
    }
  }

  const getStatusColor = (status: Project['status']) => {
    switch (status) {
      case 'draft': return 'bg-gray-100 text-gray-800'
      case 'building': return 'bg-yellow-100 text-yellow-800'
      case 'ready': return 'bg-blue-100 text-blue-800'
      case 'deployed': return 'bg-green-100 text-green-800'
      case 'error': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status: Project['status']) => {
    switch (status) {
      case 'draft': return <Edit className="h-4 w-4" />
      case 'building': return <RefreshCw className="h-4 w-4 animate-spin" />
      case 'ready': return <CheckCircle className="h-4 w-4" />
      case 'deployed': return <Globe className="h-4 w-4" />
      case 'error': return <AlertCircle className="h-4 w-4" />
      default: return <Clock className="h-4 w-4" />
    }
  }

  const getProjectTypeIcon = (type: Project['type']) => {
    switch (type) {
      case 'web': return <Globe className="h-5 w-5" />
      case 'api': return <Code className="h-5 w-5" />
      case 'agent': return <Zap className="h-5 w-5" />
      case 'ecommerce': return <Database className="h-5 w-5" />
      case 'dashboard': return <Layers className="h-5 w-5" />
      default: return <FolderOpen className="h-5 w-5" />
    }
  }

  const filteredProjects = projects.filter(project => {
    if (filter === 'all') return true
    return project.type === filter
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">TauseStack Builder 🏗️</h1>
            <p className="text-gray-600 mt-1">Crea aplicaciones sin código con potencia de IA</p>
          </div>
          <div className="flex items-center gap-3">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={loadBuilderData}
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Actualizar
            </Button>
            <Button 
              className="bg-indigo-600 hover:bg-indigo-700"
              onClick={() => setShowNewProjectModal(true)}
            >
              <Plus className="h-4 w-4 mr-2" />
              Nuevo Proyecto
            </Button>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-100 rounded-lg">
                  <FolderOpen className="h-5 w-5 text-indigo-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total Proyectos</p>
                  <p className="text-xl font-bold text-gray-900">{stats?.total_projects || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <RefreshCw className="h-5 w-5 text-yellow-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Construyendo</p>
                  <p className="text-xl font-bold text-gray-900">{stats?.active_builds || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Desplegados</p>
                  <p className="text-xl font-bold text-gray-900">{stats?.successful_deploys || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-red-100 rounded-lg">
                  <AlertCircle className="h-5 w-5 text-red-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Errores</p>
                  <p className="text-xl font-bold text-gray-900">{stats?.failed_deploys || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Layers className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Templates</p>
                  <p className="text-xl font-bold text-gray-900">{stats?.templates_used || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters and View Toggle */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Filtrar:</span>
              <select 
                value={filter} 
                onChange={(e) => setFilter(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm"
              >
                <option value="all">Todos</option>
                <option value="web">Web</option>
                <option value="api">API</option>
                <option value="agent">Agente</option>
                <option value="ecommerce">E-commerce</option>
                <option value="dashboard">Dashboard</option>
              </select>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant={view === 'grid' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setView('grid')}
            >
              <Layers className="h-4 w-4" />
            </Button>
            <Button
              variant={view === 'list' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setView('list')}
            >
              <FolderOpen className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Projects Grid */}
        <div className={`grid gap-4 ${view === 'grid' ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1'}`}>
          {filteredProjects.map(project => (
            <Card key={project.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-gray-100 rounded-lg">
                      {getProjectTypeIcon(project.type)}
                    </div>
                    <div>
                      <CardTitle className="text-lg">{project.name}</CardTitle>
                      <p className="text-sm text-gray-600">{project.description}</p>
                    </div>
                  </div>
                  <Badge className={getStatusColor(project.status)}>
                    <div className="flex items-center gap-1">
                      {getStatusIcon(project.status)}
                      {project.status}
                    </div>
                  </Badge>
                </div>
              </CardHeader>
              
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <span>Componentes: {project.components?.length || 0}</span>
                    <span>Actualizado: {new Date(project.updated_at).toLocaleDateString()}</span>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedProject(project)}
                    >
                      <Eye className="h-4 w-4 mr-1" />
                      Ver
                    </Button>
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleBuildProject(project.id)}
                      disabled={project.status === 'building'}
                    >
                      <Play className="h-4 w-4 mr-1" />
                      Build
                    </Button>
                    
                    {project.status === 'ready' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeployProject(project.id)}
                      >
                        <Globe className="h-4 w-4 mr-1" />
                        Deploy
                      </Button>
                    )}
                    
                    {project.status === 'ready' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => window.open(`/admin/builder/live-coding/${project.id}`, '_blank')}
                        className="bg-purple-50 hover:bg-purple-100 text-purple-700 border-purple-200"
                      >
                        <Code className="h-4 w-4 mr-1" />
                        Live Coding
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Empty State */}
        {filteredProjects.length === 0 && (
          <div className="text-center py-12">
            <FolderOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No hay proyectos {filter !== 'all' ? `de tipo ${filter}` : ''}
            </h3>
            <p className="text-gray-600 mb-6">
              Comienza creando tu primer proyecto con TauseStack Builder
            </p>
            <Button 
              className="bg-indigo-600 hover:bg-indigo-700"
              onClick={() => setShowNewProjectModal(true)}
            >
              <Plus className="h-4 w-4 mr-2" />
              Crear Proyecto
            </Button>
          </div>
        )}
      </div>

      {/* Modal para Nuevo Proyecto */}
      {showNewProjectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Nuevo Proyecto</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre del Proyecto
                </label>
                <input
                  type="text"
                  value={newProject.name}
                  onChange={(e) => setNewProject({...newProject, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Mi Proyecto Increíble"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descripción
                </label>
                <textarea
                  value={newProject.description}
                  onChange={(e) => setNewProject({...newProject, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  rows={3}
                  placeholder="Descripción del proyecto..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Proyecto
                </label>
                <select
                  value={newProject.type}
                  onChange={(e) => setNewProject({...newProject, type: e.target.value as Project['type']})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="web">Aplicación Web</option>
                  <option value="api">API REST</option>
                  <option value="agent">Agente IA</option>
                  <option value="ecommerce">E-commerce</option>
                  <option value="dashboard">Dashboard</option>
                </select>
              </div>
            </div>
            
            <div className="flex items-center gap-3 mt-6">
              <Button
                onClick={handleCreateProject}
                disabled={isCreating || !newProject.name.trim()}
                className="bg-indigo-600 hover:bg-indigo-700"
              >
                {isCreating ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Creando...
                  </>
                ) : (
                  <>
                    <Plus className="h-4 w-4 mr-2" />
                    Crear Proyecto
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowNewProjectModal(false)}
                disabled={isCreating}
              >
                Cancelar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
} 