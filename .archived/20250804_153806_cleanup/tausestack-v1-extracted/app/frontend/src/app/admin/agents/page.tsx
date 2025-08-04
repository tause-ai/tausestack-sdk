'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Bot, 
  Plus, 
  Play, 
  Pause, 
  Settings, 
  Trash2, 
  Activity,
  Brain,
  Clock,
  TrendingUp,
  Users,
  Zap,
  Edit,
  ShoppingCart,
  AlertCircle
} from 'lucide-react';
import Link from 'next/link';
import { ApiClient } from '@/lib/api';

interface Agent {
  agent_id: string;
  name: string;
  tenant_id: string;
  role_name: string;
  enabled: boolean;
  is_busy: boolean;
  tasks_completed: number;
  tasks_failed: number;
  total_tokens_used: number;
  total_execution_time_ms: number;
  memory_size: number;
  last_activity?: string;
}

interface DashboardStats {
  total_agents: number;
  active_agents: number;
  total_tasks_today: number;
  total_tokens_today: number;
  avg_response_time_ms: number;
  success_rate: number;
}

export default function AgentsAdminPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Cargar datos
  const loadData = async () => {
    try {
      setLoading(true);
      const [agentsRes, statsRes] = await Promise.all([
        ApiClient.get('/api/agents'),
        ApiClient.get('/api/agents/stats')
      ]);

      if (agentsRes.ok) {
        const agentsData = await agentsRes.json();
        setAgents(agentsData);
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      } else {
        // Calcular stats básicas desde agents si no hay endpoint
        const activeAgents = agents.filter(a => a.enabled).length;
        const totalTasks = agents.reduce((sum, a) => sum + a.tasks_completed, 0);
        const totalTokens = agents.reduce((sum, a) => sum + a.total_tokens_used, 0);
        const avgTime = agents.length > 0 
          ? agents.reduce((sum, a) => sum + a.total_execution_time_ms, 0) / agents.length
          : 0;
        
        setStats({
          total_agents: agents.length,
          active_agents: activeAgents,
          total_tasks_today: totalTasks,
          total_tokens_today: totalTokens,
          avg_response_time_ms: avgTime,
          success_rate: totalTasks > 0 ? ((totalTasks - agents.reduce((sum, a) => sum + a.tasks_failed, 0)) / totalTasks) * 100 : 100
        });
      }

      setError(null);
    } catch (err) {
      setError('Error cargando datos de agentes');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Alternar estado de agente
  const toggleAgent = async (agentId: string, enabled: boolean) => {
    try {
      const response = await ApiClient.put(`/api/agents/${agentId}`, { enabled: !enabled });

      if (response.ok) {
        await loadData();
      } else {
        setError('Error actualizando agente');
      }
    } catch (err) {
      setError('Error actualizando agente');
    }
  };

  // Eliminar agente
  const deleteAgent = async (agentId: string) => {
    if (!confirm('¿Estás seguro de eliminar este agente?')) return;

    try {
      const response = await ApiClient.delete(`/api/agents/${agentId}`);

      if (response.ok) {
        await loadData();
      } else {
        setError('Error eliminando agente');
      }
    } catch (err) {
      setError('Error eliminando agente');
    }
  };

  useEffect(() => {
    loadData();
    // Recargar cada 30 segundos
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (agent: Agent) => {
    if (!agent.enabled) {
      return <Badge variant="secondary">Deshabilitado</Badge>;
    }
    if (agent.is_busy) {
      return <Badge variant="destructive">Ocupado</Badge>;
    }
    return <Badge variant="default">Activo</Badge>;
  };

  const getRoleIcon = (roleName: string) => {
    const role = roleName.toLowerCase();
    if (role.includes('research')) return <Brain className="w-4 h-4" />;
    if (role.includes('writer')) return <Edit className="w-4 h-4" />;
    if (role.includes('support')) return <Users className="w-4 h-4" />;
    if (role.includes('ecommerce')) return <ShoppingCart className="w-4 h-4" />;
    return <Bot className="w-4 h-4" />;
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-96 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Agentes de IA</h1>
          <p className="text-gray-600">Gestiona tus agentes multi-tenant</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={loadData} variant="outline">
            <Activity className="w-4 h-4 mr-2" />
            Actualizar
          </Button>
          <Link href="/admin/agents/create">
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Nuevo Agente
            </Button>
          </Link>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-2 text-red-700">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Agentes</p>
                  <p className="text-2xl font-bold">{stats.total_agents}</p>
                </div>
                <Bot className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Agentes Activos</p>
                  <p className="text-2xl font-bold">{stats.active_agents}</p>
                </div>
                <Zap className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Tareas Hoy</p>
                  <p className="text-2xl font-bold">{stats.total_tasks_today}</p>
                </div>
                <TrendingUp className="w-8 h-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Tiempo Promedio</p>
                  <p className="text-2xl font-bold">{Math.round(stats.avg_response_time_ms)}ms</p>
                </div>
                <Clock className="w-8 h-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Agents List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="w-5 h-5" />
            Agentes Configurados ({agents.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {agents.length === 0 ? (
            <div className="text-center py-8">
              <Bot className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No hay agentes configurados
              </h3>
              <p className="text-gray-600 mb-4">
                Crea tu primer agente para comenzar
              </p>
              <Link href="/admin/agents/create">
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  Crear Primer Agente
                </Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {agents.map((agent) => (
                <div
                  key={agent.agent_id}
                  className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2">
                        {getRoleIcon(agent.role_name)}
                        <div>
                          <h3 className="font-medium">{agent.name}</h3>
                          <p className="text-sm text-gray-600">{agent.role_name}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Tenant:</span>
                          <span className="ml-1 font-mono">{agent.tenant_id}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Tareas:</span>
                          <span className="ml-1 font-bold text-green-600">
                            {agent.tasks_completed}
                          </span>
                          {agent.tasks_failed > 0 && (
                            <span className="ml-1 text-red-600">
                              / {agent.tasks_failed} fallos
                            </span>
                          )}
                        </div>
                        <div>
                          <span className="text-gray-600">Tokens:</span>
                          <span className="ml-1 font-mono">{agent.total_tokens_used.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Memoria:</span>
                          <span className="ml-1">{agent.memory_size} items</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {getStatusBadge(agent)}
                      
                      {/* Actions */}
                      <div className="flex gap-1">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => toggleAgent(agent.agent_id, agent.enabled)}
                          className="px-2"
                        >
                          {agent.enabled ? (
                            <Pause className="w-4 h-4" />
                          ) : (
                            <Play className="w-4 h-4" />
                          )}
                        </Button>
                        
                        <Link href={`/admin/agents/${agent.agent_id}`}>
                          <Button size="sm" variant="outline" className="px-2">
                            <Settings className="w-4 h-4" />
                          </Button>
                        </Link>
                        
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => deleteAgent(agent.agent_id)}
                          className="px-2 text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Last Activity */}
                  {agent.last_activity && (
                    <div className="mt-2 text-xs text-gray-500">
                      Última actividad: {new Date(agent.last_activity).toLocaleString()}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
} 