import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:9001';

export async function GET(request: NextRequest, { params }: { params: { type: string } }) {
  try {
    const { searchParams } = new URL(request.url);
    const tenantId = searchParams.get('tenant_id') || 'default';
    
    if (!['research', 'content'].includes(params.type)) {
      return NextResponse.json(
        { error: 'Invalid team type. Must be "research" or "content"' },
        { status: 400 }
      );
    }
    
    const response = await fetch(`${API_GATEWAY_URL}/teams/preset/${params.type}?tenant_id=${tenantId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-ID': tenantId,
        ...(process.env.NODE_ENV === 'development' && {
          'Authorization': 'Bearer dev-token'
        })
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error creating preset team:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to create preset team' },
      { status: 500 }
    );
  }
} 