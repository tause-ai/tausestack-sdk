import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // Token de autenticación para acceder al admin API
    const token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbi11c2VyLWlkLTEyMyIsImVtYWlsIjoiYWRtaW5AdGF1c2UucHJvIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInBob25lIjpudWxsLCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImF1ZCI6ImF1dGhlbnRpY2F0ZWQiLCJleHAiOjE3MzYyNzI3ODUsImlhdCI6MTczNjI2OTE4NSwiaXNzIjoic3VwYWJhc2UiLCJhcHBfbWV0YWRhdGEiOnsicm9sZXMiOlsiYWRtaW4iLCJ1c2VyIl0sInRlbmFudF9pZCI6InRhdXNlLnBybyJ9LCJ1c2VyX21ldGFkYXRhIjp7ImRpc3BsYXlfbmFtZSI6IkFkbWluIFVzZXIifX0.XJpzXr_pqoLkKsqLZ6lqSH6pWUXEcQKPHWXiJlQrDYs'
    
    // Consultar stats del admin API
    const response = await fetch('https://tausestack.dev/admin/dashboard/stats', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        'X-Tenant-ID': 'tause.pro'
      },
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    
    // Formatear respuesta para el frontend con datos reales
    const formattedData = {
      tenants: ['tause.pro'], // Datos reales del tenant
      total_tenants: data.total_tenants || 1,
      usage_stats: {
        'tause.pro': data.total_requests || 0 // Usar datos reales
      }
    }
    
    return NextResponse.json(formattedData)
  } catch (error) {
    console.error('Error fetching tenant data:', error)
    return NextResponse.json(
      { error: 'Error fetching tenant data' },
      { status: 500 }
    )
  }
} 