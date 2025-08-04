import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // Consultar health check del API Gateway
    const response = await fetch('https://tausestack.dev/health', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    
    // Formatear respuesta para el frontend
    const formattedData = {
      gateway: {
        status: data.status || 'operational',
        version: data.version || '1.0.0',
        uptime: data.uptime || 'Unknown',
        total_requests: data.total_requests || 0,
        success_rate: data.success_rate || 0,
        avg_response_time: data.avg_response_time || 0
      },
      services: data.services || {},
      overall_status: data.status || 'healthy'
    }
    
    return NextResponse.json(formattedData)
  } catch (error) {
    console.error('Error fetching health data:', error)
    return NextResponse.json(
      { error: 'Error fetching health data' },
      { status: 500 }
    )
  }
} 