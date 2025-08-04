import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:9001';

export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const response = await fetch(`${API_GATEWAY_URL}/teams/${params.id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-ID': 'default',
        ...(process.env.NODE_ENV === 'development' && {
          'Authorization': 'Bearer dev-token'
        })
      }
    });

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json(
          { error: 'Team not found' },
          { status: 404 }
        );
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching team:', error);
    return NextResponse.json(
      { error: 'Failed to fetch team' },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const body = await request.json();
    
    const response = await fetch(`${API_GATEWAY_URL}/teams/${params.id}`, {
      method: 'PUT',
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
    console.error('Error updating team:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to update team' },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const response = await fetch(`${API_GATEWAY_URL}/teams/${params.id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-ID': 'default',
        ...(process.env.NODE_ENV === 'development' && {
          'Authorization': 'Bearer dev-token'
        })
      }
    });

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json(
          { error: 'Team not found' },
          { status: 404 }
        );
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error deleting team:', error);
    return NextResponse.json(
      { error: 'Failed to delete team' },
      { status: 500 }
    );
  }
} 