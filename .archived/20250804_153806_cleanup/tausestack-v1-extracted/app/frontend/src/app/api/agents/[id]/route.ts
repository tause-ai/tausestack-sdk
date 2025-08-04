import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:9001';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const response = await fetch(`${API_GATEWAY_URL}/agents/${params.id}`, {
      headers: {
        'Authorization': request.headers.get('authorization') || '',
        'X-Tenant-ID': request.headers.get('x-tenant-id') || 'default',
      },
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Error fetching agent' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Agent GET API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json();
    
    const response = await fetch(`${API_GATEWAY_URL}/agents/${params.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': request.headers.get('authorization') || '',
        'X-Tenant-ID': request.headers.get('x-tenant-id') || 'default',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Error updating agent' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Agent PUT API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const response = await fetch(`${API_GATEWAY_URL}/agents/${params.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': request.headers.get('authorization') || '',
        'X-Tenant-ID': request.headers.get('x-tenant-id') || 'default',
      },
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Error deleting agent' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Agent DELETE API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
} 