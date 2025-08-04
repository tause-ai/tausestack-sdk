import { supabase } from './supabase'

export class ApiClient {
  static async request(url: string, options: RequestInit = {}): Promise<Response> {
    const { data: { session } } = await supabase.auth.getSession()
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    }

    // Agregar token de autenticación si existe
    if (session?.access_token) {
      headers['Authorization'] = `Bearer ${session.access_token}`
    }

    // Para desarrollo, usar API Gateway en puerto 9001 (tiene todas las rutas mapeadas)
    const baseUrl = process.env.NODE_ENV === 'development' 
      ? 'http://localhost:9001' 
      : process.env.NEXT_PUBLIC_API_URL || 'https://api.tausestack.dev'
    
    const finalUrl = url.startsWith('http') ? url : `${baseUrl}${url}`

    console.log('🔧 API Request:', {
      url: finalUrl,
      method: options.method || 'GET',
      hasAuth: !!session?.access_token
    })

    const response = await fetch(finalUrl, {
      ...options,
      headers,
    })

    return response
  }

  static async get(url: string, options: RequestInit = {}): Promise<Response> {
    return this.request(url, { ...options, method: 'GET' })
  }

  static async post(url: string, body?: any, options: RequestInit = {}): Promise<Response> {
    return this.request(url, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    })
  }

  static async put(url: string, body?: any, options: RequestInit = {}): Promise<Response> {
    return this.request(url, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    })
  }

  static async delete(url: string, options: RequestInit = {}): Promise<Response> {
    return this.request(url, { ...options, method: 'DELETE' })
  }
} 