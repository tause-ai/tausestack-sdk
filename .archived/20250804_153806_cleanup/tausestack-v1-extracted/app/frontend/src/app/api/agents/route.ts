import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:9001';

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${API_GATEWAY_URL}/agents`, {
      headers: {
        'Authorization': request.headers.get('authorization') || '',
        'X-Tenant-ID': request.headers.get('x-tenant-id') || 'default',
      },
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Error fetching agents' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Agents API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const response = await fetch(`${API_GATEWAY_URL}/agents`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': request.headers.get('authorization') || '',
        'X-Tenant-ID': request.headers.get('x-tenant-id') || 'default',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Error creating agent' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Agents POST API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
} 