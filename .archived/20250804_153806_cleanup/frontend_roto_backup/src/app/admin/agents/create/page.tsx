'use client';

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Bot, 
  Brain, 
  Edit, 
  Users, 
  ShoppingCart,
  ArrowLeft,
  Save,
  Eye,
  Settings,
  Wand2,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ApiClient } from '@/lib/api';

interface AgentRole {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  defaultTools: string[];
  examples: string[];
}

const PRESET_ROLES: AgentRole[] = [
  {
    id: 'research',
    name: 'Research Agent',
    description: 'Especializado en investigación exhaustiva y análisis de información',
    icon: <Brain className="w-5 h-5" />,
    defaultTools: ['web_search', 'data_analysis', 'summarization', 'report_generation'],
    examples: ['Investigar tendencias de mercado', 'Análizar competidores', 'Resumir papers académicos']
  },
  {
    id: 'writer',
    name: 'Content Writer',
    description: 'Experto en creación de contenido y copywriting',
    icon: <Edit className="w-5 h-5" />,
    defaultTools: ['content_generation', 'seo_optimization', 'translation', 'proofreading'],
    examples: ['Escribir blog posts', 'Crear contenido para redes', 'Optimizar SEO']
  },
  {
    id: 'customer_support',
    name: 'Customer Support',
    description: 'Asistente especializado en atención al cliente',
    icon: <Users className="w-5 h-5" />,
    defaultTools: ['ticket_management', 'knowledge_base', 'escalation', 'sentiment_analysis'],
    examples: ['Responder tickets', 'Gestionar quejas', 'Análisis de satisfacción']
  },
  {
    id: 'ecommerce',
    name: 'E-commerce Assistant',
    description: 'Optimizado para operaciones de comercio electrónico',
    icon: <ShoppingCart className="w-5 h-5" />,
    defaultTools: ['product_catalog', 'order_management', 'inventory_check', 'payment_processing'],
    examples: ['Gestionar pedidos', 'Actualizar inventario', 'Procesar pagos']
  }
];

const AVAILABLE_TOOLS = [
  { id: 'web_search', name: 'Búsqueda Web', category: 'research' },
  { id: 'data_analysis', name: 'Análisis de Datos', category: 'research' },
  { id: 'summarization', name: 'Resúmenes', category: 'research' },
  { id: 'report_generation', name: 'Generación de Reportes', category: 'research' },
  { id: 'content_generation', name: 'Generación de Contenido', category: 'writing' },
  { id: 'seo_optimization', name: 'Optimización SEO', category: 'writing' },
  { id: 'translation', name: 'Traducción', category: 'writing' },
  { id: 'proofreading', name: 'Corrección', category: 'writing' },
  { id: 'ticket_management', name: 'Gestión de Tickets', category: 'support' },
  { id: 'knowledge_base', name: 'Base de Conocimiento', category: 'support' },
  { id: 'escalation', name: 'Escalación', category: 'support' },
  { id: 'sentiment_analysis', name: 'Análisis de Sentimientos', category: 'support' },
  { id: 'product_catalog', name: 'Catálogo de Productos', category: 'ecommerce' },
  { id: 'order_management', name: 'Gestión de Pedidos', category: 'ecommerce' },
  { id: 'inventory_check', name: 'Verificación de Inventario', category: 'ecommerce' },
  { id: 'payment_processing', name: 'Procesamiento de Pagos', category: 'ecommerce' },
  { id: 'email_notifications', name: 'Notificaciones Email', category: 'general' },
  { id: 'file_storage', name: 'Almacenamiento', category: 'general' },
  { id: 'analytics_tracking', name: 'Analytics', category: 'general' }
];

export default function CreateAgentPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    tenant_id: 'default',
    role_type: '',
    custom_instructions: '',
    allowed_tools: [] as string[],
    enabled: true
  });

  const [previewMode, setPreviewMode] = useState(false);

  // Get selected role details
  const selectedRole = PRESET_ROLES.find(role => role.id === formData.role_type);

  // Handle role selection
  const handleRoleSelect = (roleId: string) => {
    const role = PRESET_ROLES.find(r => r.id === roleId);
    if (role) {
      setFormData(prev => ({
        ...prev,
        role_type: roleId,
        allowed_tools: role.defaultTools
      }));
    }
  };

  // Handle tool selection
  const toggleTool = (toolId: string) => {
    setFormData(prev => ({
      ...prev,
      allowed_tools: prev.allowed_tools.includes(toolId)
        ? prev.allowed_tools.filter(t => t !== toolId)
        : [...prev.allowed_tools, toolId]
    }));
  };

  // Submit form
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      setError('El nombre es requerido');
      return;
    }
    
    if (!formData.role_type) {
      setError('Debes seleccionar un tipo de rol');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await ApiClient.post('/api/agents', formData);

      if (response.ok) {
        setSuccess(true);
        setTimeout(() => {
          router.push('/admin/agents');
        }, 2000);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Error creando agente');
      }
    } catch (err) {
      setError('Error de conexión');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="p-6">
        <div className="max-w-2xl mx-auto text-center">
          <CheckCircle className="w-16 h-16 mx-auto text-green-500 mb-4" />
          <h2 className="text-2xl font-bold text-green-700 mb-2">
            ¡Agente Creado Exitosamente!
          </h2>
          <p className="text-gray-600 mb-4">
            Tu nuevo agente está listo para usar
          </p>
          <Button onClick={() => router.push('/admin/agents')}>
            Ver Todos los Agentes
          </Button>
        </div>
      </div>
    );
  }

  if (previewMode && selectedRole) {
    return (
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button 
              variant="outline" 
              onClick={() => setPreviewMode(false)}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Editar
            </Button>
            <div>
              <h1 className="text-3xl font-bold">Preview del Agente</h1>
              <p className="text-gray-600">Revisa la configuración antes de crear</p>
            </div>
          </div>
          <Button onClick={handleSubmit} disabled={loading} className="flex items-center gap-2">
            <Save className="w-4 h-4" />
            {loading ? 'Creando...' : 'Crear Agente'}
          </Button>
        </div>

        {/* Preview Card */}
        <Card className="max-w-4xl mx-auto">
          <CardHeader>
            <div className="flex items-center gap-4">
              {selectedRole.icon}
              <div>
                <CardTitle className="text-2xl">{formData.name}</CardTitle>
                <p className="text-gray-600">{selectedRole.name}</p>
              </div>
              <Badge variant={formData.enabled ? "default" : "secondary"}>
                {formData.enabled ? "Habilitado" : "Deshabilitado"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-sm font-medium text-gray-600">Tenant ID</Label>
                <p className="font-mono text-sm bg-gray-100 p-2 rounded">{formData.tenant_id}</p>
              </div>
              <div>
                <Label className="text-sm font-medium text-gray-600">Rol</Label>
                <p className="text-sm bg-gray-100 p-2 rounded">{selectedRole.description}</p>
              </div>
            </div>

            {/* Custom Instructions */}
            {formData.custom_instructions && (
              <div>
                <Label className="text-sm font-medium text-gray-600">Instrucciones Personalizadas</Label>
                <p className="text-sm bg-blue-50 p-3 rounded border-l-4 border-blue-400">
                  {formData.custom_instructions}
                </p>
              </div>
            )}

            {/* Tools */}
            <div>
              <Label className="text-sm font-medium text-gray-600">
                Herramientas Habilitadas ({formData.allowed_tools.length})
              </Label>
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.allowed_tools.map(toolId => {
                  const tool = AVAILABLE_TOOLS.find(t => t.id === toolId);
                  return tool ? (
                    <Badge key={toolId} variant="outline">
                      {tool.name}
                    </Badge>
                  ) : null;
                })}
              </div>
            </div>

            {/* Examples */}
            <div>
              <Label className="text-sm font-medium text-gray-600">Casos de Uso Ejemplos</Label>
              <ul className="list-disc list-inside text-sm text-gray-600 mt-2 space-y-1">
                {selectedRole.examples.map((example, idx) => (
                  <li key={idx}>{example}</li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Error */}
        {error && (
          <div className="max-w-4xl mx-auto bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-2 text-red-700">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/admin/agents">
            <Button variant="outline" className="flex items-center gap-2">
              <ArrowLeft className="w-4 h-4" />
              Volver
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">Crear Nuevo Agente</h1>
            <p className="text-gray-600">Configura un agente de IA personalizado</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={() => setPreviewMode(true)}
            disabled={!formData.name || !formData.role_type}
            className="flex items-center gap-2"
          >
            <Eye className="w-4 h-4" />
            Preview
          </Button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto space-y-8">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Información Básica
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Nombre del Agente *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Ej: Asistente de Ventas"
                  required
                />
              </div>
              <div>
                <Label htmlFor="tenant_id">Tenant ID</Label>
                <Input
                  id="tenant_id"
                  value={formData.tenant_id}
                  onChange={(e) => setFormData(prev => ({ ...prev, tenant_id: e.target.value }))}
                  placeholder="default"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="custom_instructions">Instrucciones Personalizadas</Label>
              <Textarea
                id="custom_instructions"
                value={formData.custom_instructions}
                onChange={(e) => setFormData(prev => ({ ...prev, custom_instructions: e.target.value }))}
                placeholder="Instrucciones específicas para este agente..."
                rows={3}
              />
              <p className="text-xs text-gray-500 mt-1">
                Opcional: Instrucciones específicas que el agente seguirá en todas sus interacciones
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Role Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wand2 className="w-5 h-5" />
              Seleccionar Rol
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {PRESET_ROLES.map((role) => (
                <div
                  key={role.id}
                  className={`border rounded-lg p-4 cursor-pointer transition-all ${
                    formData.role_type === role.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => handleRoleSelect(role.id)}
                >
                  <div className="flex items-center gap-3 mb-2">
                    {role.icon}
                    <h3 className="font-medium">{role.name}</h3>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{role.description}</p>
                  <div className="text-xs">
                    <span className="font-medium">Herramientas por defecto:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {role.defaultTools.slice(0, 3).map(tool => (
                        <Badge key={tool} variant="secondary" className="text-xs">
                          {AVAILABLE_TOOLS.find(t => t.id === tool)?.name || tool}
                        </Badge>
                      ))}
                      {role.defaultTools.length > 3 && (
                        <Badge variant="secondary" className="text-xs">
                          +{role.defaultTools.length - 3} más
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Tools Configuration */}
        {formData.role_type && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="w-5 h-5" />
                Configurar Herramientas
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {['research', 'writing', 'support', 'ecommerce', 'general'].map(category => {
                  const categoryTools = AVAILABLE_TOOLS.filter(tool => tool.category === category);
                  if (categoryTools.length === 0) return null;

                  return (
                    <div key={category}>
                      <h4 className="font-medium text-sm text-gray-700 mb-2 capitalize">
                        {category === 'research' ? 'Investigación' :
                         category === 'writing' ? 'Escritura' :
                         category === 'support' ? 'Soporte' :
                         category === 'ecommerce' ? 'E-commerce' :
                         'General'}
                      </h4>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                        {categoryTools.map(tool => (
                          <label
                            key={tool.id}
                            className={`flex items-center gap-2 p-2 rounded border cursor-pointer transition-colors ${
                              formData.allowed_tools.includes(tool.id)
                                ? 'border-blue-500 bg-blue-50'
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={formData.allowed_tools.includes(tool.id)}
                              onChange={() => toggleTool(tool.id)}
                              className="w-4 h-4"
                            />
                            <span className="text-sm">{tool.name}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-2 text-red-700">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        )}

        {/* Submit */}
        <div className="flex justify-end gap-4">
          <Link href="/admin/agents">
            <Button variant="outline">Cancelar</Button>
          </Link>
          <Button 
            type="submit" 
            disabled={loading || !formData.name || !formData.role_type}
            className="flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            {loading ? 'Creando...' : 'Crear Agente'}
          </Button>
        </div>
      </form>
    </div>
  );
} 