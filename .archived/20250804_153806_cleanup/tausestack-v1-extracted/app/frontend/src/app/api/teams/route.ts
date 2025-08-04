import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:9001';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const params = new URLSearchParams(searchParams);
    
    const response = await fetch(`${API_GATEWAY_URL}/teams?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-ID': 'default',
        // En producción, agregar headers de autenticación
        ...(process.env.NODE_ENV === 'development' && {
          'Authorization': 'Bearer dev-token'
        })
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching teams:', error);
    return NextResponse.json(
      { error: 'Failed to fetch teams' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const response = await fetch(`${API_GATEWAY_URL}/teams`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-ID': 'default',
        ...(process.env.NODE_ENV === 'development' && {
          'Authorization': 'Bearer dev-token'
        })
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error creating team:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to create team' },
      { status: 500 }
    );
  }
} 