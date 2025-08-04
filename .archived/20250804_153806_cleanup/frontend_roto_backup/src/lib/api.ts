/**
 * API Client para TauseStack Frontend
 * Cliente HTTP simplificado para comunicarse con las APIs del backend
 */

class TauseStackApiClient {
  private baseUrl: string

  constructor(baseUrl: string = '') {
    this.baseUrl = baseUrl
  }

  private async request(url: string, options: RequestInit = {}): Promise<Response> {
    const fullUrl = this.baseUrl + url
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(fullUrl, defaultOptions)
      return response
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  async get(url: string, options: RequestInit = {}): Promise<Response> {
    return this.request(url, {
      method: 'GET',
      ...options,
    })
  }

  async post(url: string, data?: any, options: RequestInit = {}): Promise<Response> {
    return this.request(url, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    })
  }

  async put(url: string, data?: any, options: RequestInit = {}): Promise<Response> {
    return this.request(url, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    })
  }

  async delete(url: string, options: RequestInit = {}): Promise<Response> {
    return this.request(url, {
      method: 'DELETE',
      ...options,
    })
  }

  async patch(url: string, data?: any, options: RequestInit = {}): Promise<Response> {
    return this.request(url, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    })
  }
}

// Instancia global del cliente API
export const ApiClient = new TauseStackApiClient()

// Export default para compatibilidad
export default ApiClient 