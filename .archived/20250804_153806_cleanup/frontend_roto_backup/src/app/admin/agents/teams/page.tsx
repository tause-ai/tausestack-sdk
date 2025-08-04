'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Users, 
  Plus, 
  Play, 
  Settings, 
  Trash2, 
  Activity,
  Brain,
  Edit,
  ShoppingCart,
  UserCheck,
  Zap,
  Clock,
  TrendingUp,
  ArrowLeft,
  Workflow,
  AlertCircle
} from 'lucide-react';
import Link from 'next/link';

interface AgentTeam {
  team_id: string;
  name: string;
  team_type: string;
  tenant_id: string;
  is_busy: boolean;
  agent_count: number;
  workflow_name: string;
  current_execution?: string;
  workflows_completed: number;
  workflows_failed: number;
  total_execution_time_ms: number;
  total_tokens_used: number;
  agents: Array<{
    agent_id: string;
    name: string;
    role: string;
  }>;
}

interface TeamStats {
  total_teams: number;
  active_teams: number;
  total_workflows_today: number;
  total_tokens_today: number;
  avg_workflow_time_ms: number;
  success_rate: number;
}

export default function AgentTeamsPage() {
  const [teams, setTeams] = useState<AgentTeam[]>([]);
  const [stats, setStats] = useState<TeamStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Cargar datos
  const loadData = async () => {
    try {
      setLoading(true);
      const [teamsRes, statsRes] = await Promise.all([
        fetch('/api/teams'),
        fetch('/api/teams/stats')
      ]);

      if (teamsRes.ok) {
        const teamsData = await teamsRes.json();
        setTeams(teamsData);
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      } else {
        // Calcular stats básicas desde teams si no hay endpoint
        const activeTeams = teams.filter(t => !t.is_busy).length;
        const totalWorkflows = teams.reduce((sum, t) => sum + t.workflows_completed, 0);
        const totalTokens = teams.reduce((sum, t) => sum + t.total_tokens_used, 0);
        const avgTime = teams.length > 0 
          ? teams.reduce((sum, t) => sum + t.total_execution_time_ms, 0) / teams.length
          : 0;
        
        setStats({
          total_teams: teams.length,
          active_teams: activeTeams,
          total_workflows_today: totalWorkflows,
          total_tokens_today: totalTokens,
          avg_workflow_time_ms: avgTime,
          success_rate: totalWorkflows > 0 ? 
            ((totalWorkflows - teams.reduce((sum, t) => sum + t.workflows_failed, 0)) / totalWorkflows) * 100 : 100
        });
      }

      setError(null);
    } catch (err) {
      setError('Error cargando datos de equipos');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Eliminar equipo
  const deleteTeam = async (teamId: string) => {
    if (!confirm('¿Estás seguro de eliminar este equipo?')) return;

    try {
      const response = await fetch(`/api/teams/${teamId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        await loadData();
      } else {
        setError('Error eliminando equipo');
      }
    } catch (err) {
      setError('Error eliminando equipo');
    }
  };

  // Crear equipo preset
  const createPresetTeam = async (type: 'research' | 'content') => {
    try {
      const response = await fetch(`/api/teams/preset/${type}?tenant_id=default`, {
        method: 'GET'
      });

      if (response.ok) {
        await loadData();
      } else {
        setError(`Error creando equipo ${type}`);
      }
    } catch (err) {
      setError('Error creando equipo');
    }
  };

  useEffect(() => {
    loadData();
    // Recargar cada 30 segundos
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getTeamTypeIcon = (teamType: string) => {
    switch (teamType) {
      case 'research': return <Brain className="w-4 h-4" />;
      case 'content_creation': return <Edit className="w-4 h-4" />;
      case 'customer_support': return <UserCheck className="w-4 h-4" />;
      case 'ecommerce_optimization': return <ShoppingCart className="w-4 h-4" />;
      default: return <Users className="w-4 h-4" />;
    }
  };

  const getTeamTypeName = (teamType: string) => {
    switch (teamType) {
      case 'research': return 'Investigación';
      case 'content_creation': return 'Creación de Contenido';
      case 'customer_support': return 'Soporte al Cliente';
      case 'ecommerce_optimization': return 'Optimización E-commerce';
      default: return 'Personalizado';
    }
  };

  const getStatusBadge = (team: AgentTeam) => {
    if (team.is_busy) {
      return <Badge variant="destructive">Ejecutando</Badge>;
    }
    return <Badge variant="default">Disponible</Badge>;
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
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/admin/agents">
            <Button variant="outline" className="flex items-center gap-2">
              <ArrowLeft className="w-4 h-4" />
              Agentes
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">Equipos de Agentes</h1>
            <p className="text-gray-600">Gestiona equipos con workflows coordinados</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button onClick={loadData} variant="outline">
            <Activity className="w-4 h-4 mr-2" />
            Actualizar
          </Button>
          <div className="relative">
            <Button className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Nuevo Equipo
            </Button>
            {/* Dropdown simple */}
            <div className="absolute right-0 mt-2 w-48 bg-white border rounded-lg shadow-lg z-10 hidden group-hover:block">
              <button
                onClick={() => createPresetTeam('research')}
                className="w-full text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2"
              >
                <Brain className="w-4 h-4" />
                Equipo de Investigación
              </button>
              <button
                onClick={() => createPresetTeam('content')}
                className="w-full text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2"
              >
                <Edit className="w-4 h-4" />
                Equipo de Contenido
              </button>
              <Link href="/admin/agents/teams/create">
                <div className="w-full text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2">
                  <Settings className="w-4 h-4" />
                  Equipo Personalizado
                </div>
              </Link>
            </div>
          </div>
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
                  <p className="text-sm text-gray-600">Total Equipos</p>
                  <p className="text-2xl font-bold">{stats.total_teams}</p>
                </div>
                <Users className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Equipos Disponibles</p>
                  <p className="text-2xl font-bold">{stats.active_teams}</p>
                </div>
                <Zap className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Workflows Hoy</p>
                  <p className="text-2xl font-bold">{stats.total_workflows_today}</p>
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
                  <p className="text-2xl font-bold">{Math.round(stats.avg_workflow_time_ms / 1000)}s</p>
                </div>
                <Clock className="w-8 h-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Teams List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Equipos Configurados ({teams.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {teams.length === 0 ? (
            <div className="text-center py-8">
              <Users className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No hay equipos configurados
              </h3>
              <p className="text-gray-600 mb-4">
                Crea tu primer equipo para comenzar con workflows coordinados
              </p>
              <div className="flex gap-2 justify-center">
                <Button onClick={() => createPresetTeam('research')} variant="outline">
                  <Brain className="w-4 h-4 mr-2" />
                  Equipo de Investigación
                </Button>
                <Button onClick={() => createPresetTeam('content')} variant="outline">
                  <Edit className="w-4 h-4 mr-2" />
                  Equipo de Contenido
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {teams.map((team) => (
                <div
                  key={team.team_id}
                  className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2">
                        {getTeamTypeIcon(team.team_type)}
                        <div>
                          <h3 className="font-medium">{team.name}</h3>
                          <p className="text-sm text-gray-600">{getTeamTypeName(team.team_type)}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Agentes:</span>
                          <span className="ml-1 font-bold text-blue-600">
                            {team.agent_count}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-600">Workflows:</span>
                          <span className="ml-1 font-bold text-green-600">
                            {team.workflows_completed}
                          </span>
                          {team.workflows_failed > 0 && (
                            <span className="ml-1 text-red-600">
                              / {team.workflows_failed} fallos
                            </span>
                          )}
                        </div>
                        <div>
                          <span className="text-gray-600">Tokens:</span>
                          <span className="ml-1 font-mono">{team.total_tokens_used.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Workflow:</span>
                          <span className="ml-1">{team.workflow_name}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {getStatusBadge(team)}
                      
                      {/* Actions */}
                      <div className="flex gap-1">
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={team.is_busy}
                          className="px-2"
                        >
                          <Play className="w-4 h-4" />
                        </Button>
                        
                        <Link href={`/admin/agents/teams/${team.team_id}`}>
                          <Button size="sm" variant="outline" className="px-2">
                            <Settings className="w-4 h-4" />
                          </Button>
                        </Link>
                        
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => deleteTeam(team.team_id)}
                          className="px-2 text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Team Members */}
                  <div className="mt-3 pt-3 border-t">
                    <p className="text-xs text-gray-500 mb-2">Miembros del equipo:</p>
                    <div className="flex flex-wrap gap-2">
                      {team.agents.map((agent) => (
                        <Badge key={agent.agent_id} variant="secondary" className="text-xs">
                          {agent.name} ({agent.role})
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Current Execution */}
                  {team.current_execution && (
                    <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs">
                      <div className="flex items-center gap-1">
                        <Workflow className="w-3 h-3 text-yellow-600" />
                        <span className="text-yellow-700">
                          Ejecutando workflow: {team.current_execution}
                        </span>
                      </div>
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