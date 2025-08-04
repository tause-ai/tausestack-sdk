'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  FileText, 
  Download, 
  Eye, 
  Plus,
  Search,
  Filter
} from 'lucide-react'

interface Template {
  id: string
  name: string
  description: string
  category: string
  author: string
  version: string
  tags: string[]
  downloads: number
  rating: number
  preview_image?: string
  created_at: string
}

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')

  useEffect(() => {
    // Datos de ejemplo para mostrar la interfaz
    const mockTemplates: Template[] = [
      {
        id: '1',
        name: 'Dashboard Avanzado',
        description: 'Dashboard moderno con métricas en tiempo real y gráficos interactivos',
        category: 'dashboard',
        author: 'TauseStack Team',
        version: '1.2.0',
        tags: ['dashboard', 'analytics', 'charts'],
        downloads: 1250,
        rating: 4.8,
        created_at: '2024-01-15'
      },
      {
        id: '2',
        name: 'E-commerce Store',
        description: 'Template completo para tienda online con carrito y pagos',
        category: 'ecommerce',
        author: 'TauseStack Team',
        version: '2.1.0',
        tags: ['ecommerce', 'store', 'payments'],
        downloads: 890,
        rating: 4.7,
        created_at: '2024-01-10'
      },
      {
        id: '3',
        name: 'CRM Basic',
        description: 'Sistema CRM básico para gestión de clientes y leads',
        category: 'crm',
        author: 'Community',
        version: '1.0.0',
        tags: ['crm', 'customers', 'leads'],
        downloads: 445,
        rating: 4.5,
        created_at: '2024-01-08'
      }
    ]
    
    setTimeout(() => {
      setTemplates(mockTemplates)
      setLoading(false)
    }, 1000)
  }, [])

  const categories = [
    { value: 'all', label: 'Todos' },
    { value: 'dashboard', label: 'Dashboard' },
    { value: 'ecommerce', label: 'E-commerce' },
    { value: 'crm', label: 'CRM' },
    { value: 'blog', label: 'Blog' },
    { value: 'portfolio', label: 'Portfolio' }
  ]

  const filteredTemplates = templates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         template.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory
    return matchesSearch && matchesCategory
  })

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
            <h1 className="text-2xl font-semibold text-gray-900">Templates</h1>
            <p className="text-gray-600 mt-1">Biblioteca de templates disponibles para TauseStack</p>
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Nuevo Template
          </Button>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Filters */}
        <Card>
          <CardContent className="p-4">
            <div className="flex gap-4 items-center">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Buscar templates..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-gray-500" />
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {categories.map(cat => (
                    <option key={cat.value} value={cat.value}>{cat.label}</option>
                  ))}
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Templates Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTemplates.map(template => (
            <Card key={template.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{template.name}</CardTitle>
                    <p className="text-sm text-gray-600 mt-1">by {template.author}</p>
                  </div>
                  <Badge variant="secondary">{template.category}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700 text-sm mb-4">{template.description}</p>
                
                <div className="flex flex-wrap gap-1 mb-4">
                  {template.tags.map(tag => (
                    <Badge key={tag} variant="outline" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>

                <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                  <span>v{template.version}</span>
                  <span>{template.downloads} descargas</span>
                  <span>⭐ {template.rating}</span>
                </div>

                <div className="flex gap-2">
                  <Button variant="outline" size="sm" className="flex-1">
                    <Eye className="h-4 w-4 mr-2" />
                    Preview
                  </Button>
                  <Button size="sm" className="flex-1">
                    <Download className="h-4 w-4 mr-2" />
                    Usar
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredTemplates.length === 0 && (
          <div className="text-center py-12">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No se encontraron templates</h3>
            <p className="text-gray-600">Intenta ajustar los filtros de búsqueda</p>
          </div>
        )}
      </div>
    </div>
  )
} 