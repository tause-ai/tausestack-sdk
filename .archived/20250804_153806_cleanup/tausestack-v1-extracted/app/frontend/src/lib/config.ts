/**
 * Configuración centralizada para URLs de API
 */

const isDevelopment = process.env.NODE_ENV === 'development'
const isProduction = process.env.NODE_ENV === 'production'

export const API_CONFIG = {
  // Base URL para API Gateway
  API_BASE_URL: isDevelopment 
    ? 'http://localhost:9001'
    : 'https://api.tausestack.dev',
  
  // URLs específicas para diferentes servicios
  SERVICES: {
    ADMIN: '/api/admin',
    AGENTS: '/api/agents',
    TEAMS: '/api/teams',
    HEALTH: '/health',
    TENANTS: '/admin/tenants',
    METRICS: '/metrics'
  },
  
  // Timeout para requests
  REQUEST_TIMEOUT: 10000,
  
  // Headers por defecto
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json',
    'X-Tenant-ID': 'default'
  }
}

/**
 * Construye URL completa para endpoint
 */
export function getApiUrl(endpoint: string): string {
  const baseUrl = API_CONFIG.API_BASE_URL
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  return `${baseUrl}${cleanEndpoint}`
}

/**
 * Configuración para fetch requests
 */
export function getApiConfig(options: RequestInit = {}): RequestInit {
  return {
    headers: {
      ...API_CONFIG.DEFAULT_HEADERS,
      ...options.headers
    },
    ...options
  }
}

/**
 * Fetch con timeout personalizado
 */
export async function fetchWithTimeout(url: string, options: RequestInit = {}): Promise<Response> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.REQUEST_TIMEOUT)
  
  try {
    const response = await fetch(url, {
      ...getApiConfig(options),
      signal: controller.signal
    })
    clearTimeout(timeoutId)
    return response
  } catch (error) {
    clearTimeout(timeoutId)
    throw error
  }
} 