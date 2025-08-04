"""
Domain Proxy Service for TauseStack
Handles requests from tause.pro domains using tausestack.dev certificates
"""

import os
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import RedirectResponse
import httpx
from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)

class DomainProxyService:
    """Service to proxy requests from tause.pro to tausestack.dev backend"""
    
    def __init__(self):
        self.tausestack_backend = os.getenv("TAUSESTACK_BACKEND_URL", "https://api.tausestack.dev")
        self.tause_domains = ["tause.pro", "app.tause.pro", "api.tause.pro", "www.tause.pro"]
        
    def should_proxy(self, host: str) -> bool:
        """Check if this host should be proxied"""
        return any(host == domain or host.endswith(f".{domain}") for domain in self.tause_domains)
    
    def get_proxy_url(self, request: Request) -> str:
        """Convert tause.pro URL to tausestack.dev URL"""
        original_url = str(request.url)
        parsed = urlparse(original_url)
        
        # Map tause.pro domains to tausestack.dev
        host_mapping = {
            "tause.pro": "tausestack.dev",
            "app.tause.pro": "app.tausestack.dev", 
            "api.tause.pro": "api.tausestack.dev",
            "www.tause.pro": "www.tausestack.dev"
        }
        
        new_host = host_mapping.get(parsed.hostname, parsed.hostname)
        
        # Reconstruct URL with new host
        new_url = urlunparse((
            parsed.scheme,
            new_host,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        return new_url
    
    async def proxy_request(self, request: Request) -> Response:
        """Proxy request to tausestack.dev backend"""
        try:
            proxy_url = self.get_proxy_url(request)
            
            # Extract request details
            headers = dict(request.headers)
            
            # Update Host header
            headers["Host"] = urlparse(proxy_url).hostname
            
            # Remove potentially problematic headers
            headers.pop("host", None)
            headers.pop("content-length", None)
            
            # Make request to backend
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                if request.method == "GET":
                    response = await client.get(
                        proxy_url,
                        headers=headers,
                        params=request.query_params
                    )
                elif request.method == "POST":
                    body = await request.body()
                    response = await client.post(
                        proxy_url,
                        headers=headers,
                        content=body,
                        params=request.query_params
                    )
                elif request.method == "PUT":
                    body = await request.body()
                    response = await client.put(
                        proxy_url,
                        headers=headers,
                        content=body,
                        params=request.query_params
                    )
                elif request.method == "DELETE":
                    response = await client.delete(
                        proxy_url,
                        headers=headers,
                        params=request.query_params
                    )
                else:
                    raise HTTPException(status_code=405, detail="Method not allowed")
                
                # Forward response
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.headers.get("content-type")
                )
                
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            raise HTTPException(status_code=502, detail="Bad Gateway")

# FastAPI app for domain proxy
proxy_app = FastAPI(title="TausePro Domain Proxy")
proxy_service = DomainProxyService()

@proxy_app.middleware("http")
async def domain_proxy_middleware(request: Request, call_next):
    """Middleware to handle domain proxying"""
    host = request.headers.get("host", "").lower()
    
    # If it's a tause.pro domain, proxy to tausestack.dev
    if proxy_service.should_proxy(host):
        return await proxy_service.proxy_request(request)
    
    # Otherwise, process normally
    response = await call_next(request)
    return response

@proxy_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "domain_proxy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(proxy_app, host="0.0.0.0", port=8000) 