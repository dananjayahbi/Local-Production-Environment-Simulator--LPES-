"""
HTTPS reverse proxy server for LPES.
Handles SSL termination and request forwarding to local development servers.
"""

import asyncio
import logging
import ssl
from typing import Dict, Optional, Callable, Any
from urllib.parse import urlparse

import aiohttp
from aiohttp import web, ClientSession
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from lpes.core.config import LPESConfig
from lpes.core.project_manager import ProjectManager
from lpes.ssl.manager import SSLManager


logger = logging.getLogger(__name__)


class ProxyServer:
    """HTTPS reverse proxy server for LPES."""
    
    def __init__(self, 
                 config: Optional[LPESConfig] = None,
                 project_manager: Optional[ProjectManager] = None,
                 ssl_manager: Optional[SSLManager] = None):
        self.config = config or LPESConfig()
        self.project_manager = project_manager or ProjectManager(self.config)
        self.ssl_manager = ssl_manager or SSLManager(self.config)
        
        self.app = web.Application()
        self.setup_routes()
        
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self.is_running = False
        
        # Store active SSL contexts by domain
        self._ssl_contexts: Dict[str, ssl.SSLContext] = {}
        
        # WebSocket connections for real-time features
        self._websocket_connections: Dict[str, set] = {}
    
    def setup_routes(self):
        """Setup proxy routes."""
        # Catch-all route for proxying
        self.app.router.add_route('*', '/{path:.*}', self.handle_request)
        
        # WebSocket support
        self.app.router.add_get('/_lpes/ws', self.handle_websocket)
        
        # Health check endpoint
        self.app.router.add_get('/_lpes/health', self.handle_health)
    
    async def handle_request(self, request: Request) -> Response:
        """Handle incoming HTTP/HTTPS requests."""
        try:
            # Get the target project based on the Host header
            host = request.host
            if ':' in host:
                domain = host.split(':')[0]
            else:
                domain = host
            
            logger.debug(f"Handling request for {domain}: {request.method} {request.path}")
            
            # Find the project for this domain
            project = self.project_manager.get_project_by_domain(domain)
            if not project:
                logger.warning(f"No project found for domain: {domain}")
                return web.Response(
                    text=f"No project configured for domain: {domain}",
                    status=404
                )
            
            if not project.is_running:
                logger.warning(f"Project {project.name} is not running")
                return web.Response(
                    text=f"Project {project.name} is not running. Please start it first.",
                    status=503
                )
            
            # Forward the request to the local server
            target_url = f"http://localhost:{project.config.start.port}{request.path_qs}"
            
            return await self._forward_request(request, target_url, project)
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return web.Response(
                text=f"Internal proxy error: {str(e)}",
                status=500
            )
    
    async def _forward_request(self, request: Request, target_url: str, project) -> Response:
        """Forward request to the target server."""
        try:
            # Prepare headers
            headers = dict(request.headers)
            
            # Remove hop-by-hop headers
            hop_by_hop = {
                'connection', 'keep-alive', 'proxy-authenticate',
                'proxy-authorization', 'te', 'trailers', 'upgrade'
            }
            headers = {k: v for k, v in headers.items() if k.lower() not in hop_by_hop}
            
            # Set forwarded headers
            headers['X-Forwarded-For'] = request.remote
            headers['X-Forwarded-Proto'] = 'https' if request.secure else 'http'
            headers['X-Forwarded-Host'] = request.host
            
            # Handle request body
            body = None
            if request.method in ['POST', 'PUT', 'PATCH']:
                body = await request.read()
            
            # Make the request to the target server
            timeout = aiohttp.ClientTimeout(total=30)
            async with ClientSession(timeout=timeout) as session:
                async with session.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    data=body,
                    allow_redirects=False
                ) as target_response:
                    
                    # Prepare response headers
                    response_headers = dict(target_response.headers)
                    
                    # Remove hop-by-hop headers from response
                    response_headers = {
                        k: v for k, v in response_headers.items() 
                        if k.lower() not in hop_by_hop
                    }
                    
                    # Add security headers for HTTPS
                    if request.secure:
                        response_headers.update({
                            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                            'X-Content-Type-Options': 'nosniff',
                            'X-Frame-Options': 'SAMEORIGIN',
                            'X-XSS-Protection': '1; mode=block'
                        })
                    
                    # Read response body
                    response_body = await target_response.read()
                    
                    # Create response
                    response = web.Response(
                        body=response_body,
                        status=target_response.status,
                        headers=response_headers
                    )
                    
                    logger.debug(
                        f"Forwarded {request.method} {request.path} -> "
                        f"{target_response.status} ({len(response_body)} bytes)"
                    )
                    
                    return response
                    
        except aiohttp.ClientConnectorError:
            logger.error(f"Cannot connect to target server: {target_url}")
            return web.Response(
                text=f"Cannot connect to {project.name}. Is the development server running?",
                status=502
            )
        except asyncio.TimeoutError:
            logger.error(f"Timeout connecting to target server: {target_url}")
            return web.Response(
                text=f"Timeout connecting to {project.name}",
                status=504
            )
        except Exception as e:
            logger.error(f"Error forwarding request: {e}")
            return web.Response(
                text=f"Proxy error: {str(e)}",
                status=500
            )
    
    async def handle_websocket(self, request: Request) -> web.WebSocketResponse:
        """Handle WebSocket connections for real-time features."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        client_id = f"{request.remote}:{id(ws)}"
        domain = request.host.split(':')[0]
        
        if domain not in self._websocket_connections:
            self._websocket_connections[domain] = set()
        
        self._websocket_connections[domain].add(ws)
        logger.debug(f"WebSocket connected: {client_id} for {domain}")
        
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    # Echo or handle WebSocket messages
                    data = msg.json()
                    await ws.send_str(f"Echo: {data}")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
                    break
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self._websocket_connections[domain].discard(ws)
            logger.debug(f"WebSocket disconnected: {client_id}")
        
        return ws
    
    async def handle_health(self, request: Request) -> Response:
        """Handle health check requests."""
        projects = self.project_manager.list_projects()
        running_projects = [p for p in projects if p.is_running]
        
        health_data = {
            'status': 'healthy',
            'proxy_running': self.is_running,
            'total_projects': len(projects),
            'running_projects': len(running_projects),
            'projects': [
                {
                    'name': p.name,
                    'status': 'running' if p.is_running else 'stopped',
                    'domains': p.get_all_domains()
                }
                for p in projects
            ]
        }
        
        return web.json_response(health_data)
    
    async def broadcast_to_domain(self, domain: str, message: Dict[str, Any]):
        """Broadcast a message to all WebSocket connections for a domain."""
        if domain in self._websocket_connections:
            disconnected = set()
            for ws in self._websocket_connections[domain]:
                try:
                    await ws.send_str(str(message))
                except Exception:
                    disconnected.add(ws)
            
            # Clean up disconnected connections
            self._websocket_connections[domain] -= disconnected
    
    def _get_ssl_context_for_domain(self, domain: str) -> ssl.SSLContext:
        """Get or create SSL context for a domain."""
        if domain not in self._ssl_contexts:
            try:
                context = self.ssl_manager.get_ssl_context(domain)
                self._ssl_contexts[domain] = context
                logger.info(f"Created SSL context for {domain}")
            except Exception as e:
                logger.error(f"Failed to create SSL context for {domain}: {e}")
                raise
        
        return self._ssl_contexts[domain]
    
    async def start(self, port: int = 443, fallback_port: int = 8443) -> bool:
        """Start the proxy server."""
        if self.is_running:
            logger.warning("Proxy server is already running")
            return True
        
        try:
            logger.info(f"Starting HTTPS proxy server on port {port}")
            
            # Create app runner
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            # Try to bind to the specified port, fallback if needed
            actual_port = port
            try:
                # Create SSL context for the primary domain or default
                projects = self.project_manager.list_projects()
                if projects and projects[0].get_primary_domain():
                    domain = projects[0].get_primary_domain()
                    ssl_context = self._get_ssl_context_for_domain(domain)
                else:
                    # Create a default SSL context
                    ssl_context = self.ssl_manager.get_ssl_context("localhost")
                
                self.site = web.TCPSite(
                    self.runner,
                    'localhost',
                    actual_port,
                    ssl_context=ssl_context
                )
                await self.site.start()
                
            except OSError as e:
                if "Permission denied" in str(e) or "Address already in use" in str(e):
                    logger.warning(f"Cannot bind to port {port}, trying fallback port {fallback_port}")
                    actual_port = fallback_port
                    
                    # Create SSL context for fallback
                    if projects and projects[0].get_primary_domain():
                        domain = projects[0].get_primary_domain()
                        ssl_context = self._get_ssl_context_for_domain(domain)
                    else:
                        ssl_context = self.ssl_manager.get_ssl_context("localhost")
                    
                    self.site = web.TCPSite(
                        self.runner,
                        'localhost',
                        actual_port,
                        ssl_context=ssl_context
                    )
                    await self.site.start()
                else:
                    raise
            
            self.is_running = True
            logger.info(f"HTTPS proxy server started on https://localhost:{actual_port}")
            
            if actual_port != port:
                logger.warning(
                    f"Server running on port {actual_port} instead of {port}. "
                    f"You may need administrator privileges to bind to port {port}."
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start proxy server: {e}")
            if self.runner:
                await self.runner.cleanup()
            self.is_running = False
            return False
    
    async def stop(self) -> bool:
        """Stop the proxy server."""
        if not self.is_running:
            logger.warning("Proxy server is not running")
            return True
        
        try:
            logger.info("Stopping HTTPS proxy server")
            
            # Close all WebSocket connections
            for domain_connections in self._websocket_connections.values():
                for ws in domain_connections:
                    await ws.close()
            self._websocket_connections.clear()
            
            # Stop the server
            if self.site:
                await self.site.stop()
            
            if self.runner:
                await self.runner.cleanup()
            
            self.is_running = False
            self._ssl_contexts.clear()
            
            logger.info("HTTPS proxy server stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop proxy server: {e}")
            return False
    
    async def reload_ssl_contexts(self):
        """Reload SSL contexts for all domains."""
        logger.info("Reloading SSL contexts")
        self._ssl_contexts.clear()
        
        # Pre-load SSL contexts for all configured domains
        projects = self.project_manager.list_projects()
        for project in projects:
            for domain in project.get_all_domains():
                try:
                    self._get_ssl_context_for_domain(domain)
                except Exception as e:
                    logger.error(f"Failed to reload SSL context for {domain}: {e}")
    
    def add_domain_ssl_context(self, domain: str):
        """Add SSL context for a new domain."""
        try:
            self._get_ssl_context_for_domain(domain)
            logger.info(f"Added SSL context for new domain: {domain}")
        except Exception as e:
            logger.error(f"Failed to add SSL context for {domain}: {e}")
    
    def remove_domain_ssl_context(self, domain: str):
        """Remove SSL context for a domain."""
        if domain in self._ssl_contexts:
            del self._ssl_contexts[domain]
            logger.info(f"Removed SSL context for domain: {domain}")


class ProxyMiddleware:
    """Middleware for request/response modification."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request) -> Response:
        """Process request through middleware."""
        # Add custom headers or modify request
        request['lpes_processed'] = True
        
        # Process request
        response = await self.app(request)
        
        # Add custom response headers
        response.headers['X-Powered-By'] = 'LPES'
        response.headers['X-LPES-Version'] = '0.1.0'
        
        return response
