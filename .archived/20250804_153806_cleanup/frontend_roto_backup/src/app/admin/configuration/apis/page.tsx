"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, Settings, Trash2, CheckCircle, XCircle, Activity, RefreshCw } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { getApiUrl, fetchWithTimeout } from '@/lib/config';

// Tipos de datos
interface APIConfig {
  id: string;
  name: string;
  type: 'ai' | 'payment' | 'external';
  status: 'active' | 'inactive' | 'error';
  endpoint?: string;
  api_key?: string;
  description: string;
  last_check: string;
  config_data: Record<string, any>;
}

interface HealthCheckResult {
  api_id: string;
  status: 'active' | 'inactive' | 'error';
  latency_ms?: number;
  error_message?: string;
  timestamp: string;
}

interface DashboardStats {
  total_apis: number;
  active_apis: number;
  inactive_apis: number;
  success_rate: number;
  last_check: string;
  health_checks_today: number;
}

export default function APIsConfigPage() {
  const [activeTab, setActiveTab] = useState("configuration");
  const [apis, setApis] = useState<APIConfig[]>([]);
  const [healthResults, setHealthResults] = useState<HealthCheckResult[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [apiToDelete, setApiToDelete] = useState<string | null>(null);
  const [isHealthCheckRunning, setIsHealthCheckRunning] = useState(false);

  // Formulario para nueva API
  const [newApiForm, setNewApiForm] = useState({
    name: '',
    type: 'ai' as 'ai' | 'payment' | 'external',
    endpoint: '',
    api_key: '',
    description: '',
    config_data: {}
  });

  // Cargar datos iniciales
  useEffect(() => {
    loadApis();
    loadDashboardStats();
  }, []);

  // Funciones de API
  const loadApis = async () => {
    try {
      const response = await fetchWithTimeout(getApiUrl('/api/admin/apis'));
      if (!response.ok) throw new Error('Error al cargar APIs');
      const data = await response.json();
      setApis(data);
    } catch (error) {
      console.error('Error cargando APIs:', error);
      toast.error('Error al cargar las APIs');
    } finally {
      setLoading(false);
    }
  };

  const loadDashboardStats = async () => {
    try {
      const response = await fetchWithTimeout(getApiUrl('/api/admin/dashboard/stats'));
      if (!response.ok) throw new Error('Error al cargar estadísticas');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error cargando estadísticas:', error);
    }
  };

  const createApi = async () => {
    try {
      const response = await fetchWithTimeout(getApiUrl('/api/admin/apis'), {
        method: 'POST',
        body: JSON.stringify(newApiForm)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al crear API');
      }

      const newApi = await response.json();
      setApis([...apis, newApi]);
      setIsAddDialogOpen(false);
      setNewApiForm({
        name: '',
        type: 'ai',
        endpoint: '',
        api_key: '',
        description: '',
        config_data: {}
      });
      toast.success('API creada exitosamente');
      loadDashboardStats();
    } catch (error) {
      console.error('Error creando API:', error);
      toast.error(error instanceof Error ? error.message : 'Error al crear API');
    }
  };

  const deleteApi = async (apiId: string) => {
    try {
      const response = await fetchWithTimeout(getApiUrl(`/api/admin/apis/${apiId}`), {
        method: 'DELETE'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al eliminar API');
      }

      setApis(apis.filter(api => api.id !== apiId));
      setApiToDelete(null);
      toast.success('API eliminada exitosamente');
      loadDashboardStats();
    } catch (error) {
      console.error('Error eliminando API:', error);
      toast.error(error instanceof Error ? error.message : 'Error al eliminar API');
    }
  };

  const testApiConnection = async (apiId: string) => {
    try {
      const response = await fetchWithTimeout(getApiUrl(`/api/admin/apis/${apiId}/test`), {
        method: 'POST'
      });

      if (!response.ok) throw new Error('Error al probar conexión');
      
      const result = await response.json();
      
      // Actualizar estado de la API
      setApis(apis.map(api => 
        api.id === apiId 
          ? { ...api, status: result.status, last_check: result.timestamp }
          : api
      ));

      if (result.status === 'active') {
        toast.success(`Conexión exitosa - ${result.latency_ms}ms`);
      } else {
        toast.error(`Conexión fallida: ${result.error_message || 'Error desconocido'}`);
      }
    } catch (error) {
      console.error('Error probando conexión:', error);
      toast.error('Error al probar conexión');
    }
  };

  const runHealthCheckAll = async () => {
    setIsHealthCheckRunning(true);
    try {
      const response = await fetchWithTimeout(getApiUrl('/api/admin/health-check-all'), {
        method: 'POST'
      });

      if (!response.ok) throw new Error('Error al ejecutar health check');
      
      const results = await response.json();
      setHealthResults(results);
      
      // Actualizar estado de las APIs
      results.forEach((result: HealthCheckResult) => {
        setApis(prevApis => 
          prevApis.map(api => 
            api.id === result.api_id 
              ? { ...api, status: result.status, last_check: result.timestamp }
              : api
          )
        );
      });

      toast.success('Health check completado');
      loadDashboardStats();
    } catch (error) {
      console.error('Error en health check:', error);
      toast.error('Error al ejecutar health check');
    } finally {
      setIsHealthCheckRunning(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="default" className="bg-green-100 text-green-800">
          <CheckCircle className="w-3 h-3 mr-1" /> Activo
        </Badge>;
      case 'inactive':
        return <Badge variant="secondary">
          <XCircle className="w-3 h-3 mr-1" /> Inactivo
        </Badge>;
      case 'error':
        return <Badge variant="destructive">
          <XCircle className="w-3 h-3 mr-1" /> Error
        </Badge>;
      default:
        return <Badge variant="outline">Desconocido</Badge>;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Configuración de APIs</h1>
        </div>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Configuración de APIs</h1>
        <Button 
          onClick={runHealthCheckAll}
          disabled={isHealthCheckRunning}
          className="bg-blue-600 hover:bg-blue-700"
        >
          {isHealthCheckRunning ? (
            <>
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              Ejecutando...
            </>
          ) : (
            <>
              <Activity className="w-4 h-4 mr-2" />
              Health Check
            </>
          )}
        </Button>
      </div>

      {/* Estadísticas */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-600">Total APIs</p>
                <div className="text-2xl font-bold">{stats.total_apis}</div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-600">Activas</p>
                <div className="text-2xl font-bold text-green-600">{stats.active_apis}</div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-600">Inactivas</p>
                <div className="text-2xl font-bold text-yellow-600">{stats.inactive_apis}</div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-600">Tasa de Éxito</p>
                <div className="text-2xl font-bold">{stats.success_rate}%</div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="configuration">Configuración</TabsTrigger>
          <TabsTrigger value="health">Salud</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="configuration" className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">APIs de Inteligencia Artificial</h2>
            <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="w-4 h-4 mr-2" />
                  Agregar API
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Agregar Nueva API</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="name">Nombre</Label>
                    <Input
                      id="name"
                      value={newApiForm.name}
                      onChange={(e) => setNewApiForm({...newApiForm, name: e.target.value})}
                      placeholder="Ej: GPT-4 Custom"
                    />
                  </div>
                  <div>
                    <Label htmlFor="type">Tipo</Label>
                    <Select value={newApiForm.type} onValueChange={(value: 'ai' | 'payment' | 'external') => setNewApiForm({...newApiForm, type: value})}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="ai">Inteligencia Artificial</SelectItem>
                        <SelectItem value="payment">Pasarela de Pago</SelectItem>
                        <SelectItem value="external">API Externa</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="endpoint">URL del Endpoint</Label>
                    <Input
                      id="endpoint"
                      value={newApiForm.endpoint}
                      onChange={(e) => setNewApiForm({...newApiForm, endpoint: e.target.value})}
                      placeholder="https://api.example.com/v1"
                    />
                  </div>
                  <div>
                    <Label htmlFor="api_key">API Key</Label>
                    <Input
                      id="api_key"
                      type="password"
                      value={newApiForm.api_key}
                      onChange={(e) => setNewApiForm({...newApiForm, api_key: e.target.value})}
                      placeholder="sk-..."
                    />
                  </div>
                  <div>
                    <Label htmlFor="description">Descripción</Label>
                    <Input
                      id="description"
                      value={newApiForm.description}
                      onChange={(e) => setNewApiForm({...newApiForm, description: e.target.value})}
                      placeholder="Descripción de la API"
                    />
                  </div>
                  <div className="flex justify-end space-x-2">
                    <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                      Cancelar
                    </Button>
                    <Button 
                      onClick={createApi}
                      disabled={!newApiForm.name || !newApiForm.endpoint || !newApiForm.api_key}
                    >
                      Crear API
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {apis.filter(api => api.type === 'ai').map(api => (
              <Card key={api.id} className="relative">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{api.name}</CardTitle>
                    <div className="flex items-center space-x-2">
                      {getStatusBadge(api.status)}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => testApiConnection(api.id)}
                      >
                        <Activity className="w-4 h-4" />
                      </Button>
                      {!['openai', 'claude'].includes(api.id) && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setApiToDelete(api.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <p className="text-sm text-gray-600">{api.description}</p>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>Endpoint: {api.endpoint}</span>
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>Último check: {formatDate(api.last_check)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="health" className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Estado de Salud de las APIs</h2>
          </div>
          
          {healthResults.length > 0 ? (
            <div className="space-y-4">
              {healthResults.map((result, index) => (
                <Card key={index}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium">{apis.find(api => api.id === result.api_id)?.name}</h3>
                        <p className="text-sm text-gray-500">{formatDate(result.timestamp)}</p>
                      </div>
                      <div className="flex items-center space-x-4">
                        {result.latency_ms && (
                          <span className="text-sm text-gray-600">{result.latency_ms}ms</span>
                        )}
                        {getStatusBadge(result.status)}
                      </div>
                    </div>
                    {result.error_message && (
                      <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded">
                        <p className="text-sm text-red-800">{result.error_message}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <p className="text-gray-500">No hay resultados de health check disponibles</p>
                <p className="text-sm text-gray-400 mt-2">Ejecuta un health check para ver los resultados</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Logs del Sistema</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-500">Funcionalidad de logs en desarrollo</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Dialog de confirmación para eliminar */}
      <AlertDialog open={!!apiToDelete} onOpenChange={() => setApiToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Estás seguro?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta acción no se puede deshacer. Esto eliminará permanentemente la configuración de la API.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction 
              onClick={() => apiToDelete && deleteApi(apiToDelete)}
              className="bg-red-600 hover:bg-red-700"
            >
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
} 