### local-prod-simulator-plan-part-01

# Local Production Environment Simulator (LPES)
## Project Plan Document

### Executive Summary

The Local Production Environment Simulator (LPES) is a Python-based development tool designed to replicate production server environments on local machines. It enables developers to test web applications, particularly NextJS applications, with production-like configurations including HTTPS, custom domain names, and SSL certificates. This eliminates the need for constant deployment to cloud servers for testing production-specific issues.

---

## 1. Project Overview

### 1.1 Problem Statement

Development environments often differ significantly from production environments, leading to issues that only manifest in production. Specifically:
- NextJS Image component behaves differently with HTTPS vs HTTP
- Local development typically uses localhost:3000 while production uses proper domains
- SSL/TLS certificate handling differs between environments
- CDN and asset loading behavior varies
- Security policies (CORS, CSP) affect functionality differently

### 1.2 Solution Approach

LPES creates a local environment that mimics production by:
- Intercepting DNS requests for custom domains
- Generating and managing SSL certificates
- Proxying requests to local development servers
- Providing build and deployment automation
- Offering comprehensive logging and debugging tools

### 1.3 Key Benefits

- **Immediate Feedback**: Test production configurations without deployment delays
- **Cost Reduction**: Minimize cloud resource usage during development
- **Enhanced Debugging**: Full access to local logs and debugging tools
- **Team Collaboration**: Standardized local testing environment
- **Security**: Test SSL/HTTPS configurations locally

---

## 2. Technical Architecture

### 2.1 System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        LPES System                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Core Controller (Python)                │   │
│  │  - Project Manager                                   │   │
│  │  - Process Supervisor                                │   │
│  │  - Configuration Handler                             │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                 │
│   ┌────────────┬──────────┴┬───────────────┐                │
│   ▼            ▼           ▼               ▼                │
│ ┌──────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐       │
│ │ DNS  │ │   SSL    │ │  Proxy   │ │ Build & Deploy │       │
│ │Server│ │ Manager  │ │  Server  │ │    Engine      │       │
│ └──────┘ └──────────┘ └──────────┘ └────────────────┘       │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              User Interface Layer                    │   │
│  │  - CLI Interface                                     │   │
│  │  - Web Dashboard (Optional)                          │   │
│  │  - Real-time Console                                 │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Core Technologies

#### Primary Stack
- **Python 3.9+**: Core application logic
- **asyncio**: Asynchronous operations and process management
- **aiohttp**: HTTP server and reverse proxy functionality
- **cryptography**: SSL certificate generation and management
- **dnspython**: DNS server implementation
- **psutil**: System process monitoring

#### Supporting Libraries
- **click**: Command-line interface framework
- **rich**: Enhanced terminal output and formatting
- **pydantic**: Configuration validation and management
- **watchdog**: File system monitoring for hot-reload
- **jinja2**: Template rendering for web dashboard
- **websockets**: Real-time log streaming
- **PyYAML**: Configuration file parsing

### 2.3 Data Flow Architecture

```
Browser Request → Custom Domain (e.g., news.com)
       ↓
Local DNS Resolution (127.0.0.1)
       ↓
HTTPS Reverse Proxy (Port 443)
       ↓
SSL Termination & Certificate Validation
       ↓
Request Forwarding to NextJS App
       ↓
Response with Proper Headers
       ↓
Browser Receives HTTPS Response
```

---

## 3. Feature Specifications

### 3.1 Project Management

#### 3.1.1 Project Registration
- **Functionality**: Register NextJS projects with LPES
- **Implementation**:
  ```python
  class ProjectManager:
      def register_project(self, 
                          project_path: str,
                          build_command: str,
                          start_command: str,
                          env_variables: dict) -> Project
  ```
- **Data Storage**: SQLite database for project configurations
- **Validation**: Path existence, command validity, dependency checks

#### 3.1.2 Configuration Management
- **Project Configuration File** (`lpes.config.yaml`):
  ```yaml
  project:
    name: "my-nextjs-app"
    path: "/home/user/projects/nextjs-app"
    build:
      command: "npm run build"
      env:
        NODE_ENV: "production"
        NEXT_PUBLIC_API_URL: "https://api.example.com"
    start:
      command: "npm run start"
      port: 3000
    domains:
      - primary: "news.com"
        aliases: ["www.news.com", "blog.news.com"]
    ssl:
      auto_generate: true
      cert_path: null  # Optional custom certificate
  ```

### 3.2 Build System Integration

#### 3.2.1 Build Pipeline
- **Pre-build Hooks**: Environment setup, dependency installation
- **Build Execution**: Subprocess management with real-time output
- **Error Handling**: Graceful failure with detailed error logs
- **Build Caching**: Incremental builds and artifact caching

#### 3.2.2 Build Progress Monitoring
```python
class BuildMonitor:
    async def execute_build(self, project: Project):
        async with self.create_build_session() as session:
            await session.run_prebuild_checks()
            await session.execute_command(
                project.build_command,
                on_output=self.stream_to_console,
                on_error=self.handle_build_error
            )
            await session.verify_build_artifacts()
```

### 3.3 Domain Management System

#### 3.3.1 Local DNS Server
- **Implementation**: Python-based DNS server using `dnslib`
- **Features**:
  - Dynamic A record creation for custom domains
  - Wildcard subdomain support
  - DNS caching for performance
  - Fallback to system DNS for non-managed domains

#### 3.3.2 Hosts File Management
- **Alternative Approach**: Direct modification of system hosts file
- **Implementation**:
  ```python
  class HostsFileManager:
      def add_domain(self, domain: str, ip: str = "127.0.0.1"):
          # Platform-specific hosts file location
          hosts_path = self.get_hosts_path()
          with open(hosts_path, 'a') as f:
              f.write(f"\n{ip} {domain} www.{domain}\n")
      
      def remove_domain(self, domain: str):
          # Safe removal with backup
          pass
  ```
- **Permissions**: Require elevated privileges (sudo/admin)

### 3.4 SSL Certificate Management

#### 3.4.1 Certificate Generation
- **Self-Signed Certificates**:
  ```python
  class SSLManager:
      def generate_self_signed_cert(self, domain: str):
          key = rsa.generate_private_key(
              public_exponent=65537,
              key_size=2048
          )
          cert = x509.CertificateBuilder()
          cert = cert.subject_name(x509.Name([
              x509.NameAttribute(NameOID.COMMON_NAME, domain)
          ]))
          cert = cert.issuer_name(cert.subject)
          cert = cert.public_key(key.public_key())
          cert = cert.serial_number(x509.random_serial_number())
          cert = cert.not_valid_before(datetime.utcnow())
          cert = cert.not_valid_after(
              datetime.utcnow() + timedelta(days=365)
          )
          # Add SAN for subdomains
          cert = cert.add_extension(
              x509.SubjectAlternativeName([
                  x509.DNSName(domain),
                  x509.DNSName(f"*.{domain}")
              ]),
              critical=False,
          )
          return cert.sign(key, hashes.SHA256())
  ```

#### 3.4.2 Certificate Trust Management
- **Local CA Creation**: Generate a local Certificate Authority
- **Browser Trust**: Instructions for adding CA to browser trust stores
- **Automatic Trust** (Optional): Platform-specific trust store modification

### 3.5 Reverse Proxy Server

#### 3.5.1 HTTPS Server Implementation
```python
class ProxyServer:
    def __init__(self, ssl_context):
        self.ssl_context = ssl_context
        self.app = web.Application()
        self.setup_routes()
    
    async def handle_request(self, request):
        # Extract target from domain mapping
        target = self.get_target_for_domain(request.host)
        
        # Forward request to local NextJS server
        async with aiohttp.ClientSession() as session:
            url = f"http://localhost:{target.port}{request.path_qs}"
            async with session.request(
                method=request.method,
                url=url,
                headers=self.prepare_headers(request.headers),
                data=await request.read()
            ) as response:
                body = await response.read()
                return web.Response(
                    body=body,
                    status=response.status,
                    headers=response.headers
                )
```

#### 3.5.2 WebSocket Support
- **Implementation**: Bidirectional WebSocket proxying
- **Use Case**: NextJS hot reload, real-time features

### 3.6 Process Management

#### 3.6.1 Application Lifecycle
```python
class ProcessSupervisor:
    async def start_application(self, project: Project):
        process = await asyncio.create_subprocess_shell(
            project.start_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=project.path,
            env=self.prepare_environment(project)
        )
        
        # Monitor process health
        asyncio.create_task(self.monitor_process(process))
        
        # Stream logs
        asyncio.create_task(self.stream_logs(process))
        
        return process
```

#### 3.6.2 Health Monitoring
- **Port Availability Check**: Ensure target ports are free
- **Process Health**: Monitor CPU, memory usage
- **Automatic Restart**: On crash with backoff strategy
- **Graceful Shutdown**: Proper cleanup on exit

### 3.7 Console Interface

#### 3.7.1 Interactive CLI
```python
@click.group()
def cli():
    """LPES - Local Production Environment Simulator"""
    pass

@cli.command()
@click.option('--path', required=True, help='Project root path')
@click.option('--build', required=True, help='Build command')
@click.option('--start', required=True, help='Start command')
@click.option('--domain', prompt=True, help='Custom domain name')
def init(path, build, start, domain):
    """Initialize a new project"""
    manager = ProjectManager()
    project = manager.create_project(path, build, start)
    project.add_domain(domain)
    
    # Generate SSL certificate
    ssl_manager = SSLManager()
    cert = ssl_manager.generate_certificate(domain)
    
    # Start services
    asyncio.run(start_services(project))
```

#### 3.7.2 Real-time Console Output
- **Log Streaming**: Color-coded output (info, warning, error)
- **Progress Indicators**: Build progress, server startup
- **Interactive Commands**: While running (restart, rebuild, logs)

### 3.8 Web Dashboard (Optional Enhancement)

#### 3.8.1 Dashboard Features
- **Project Overview**: List of registered projects
- **Domain Management**: Add/remove domains, view certificates
- **Log Viewer**: Real-time log streaming with filtering
- **Metrics**: Request count, response times, error rates
- **Configuration Editor**: Modify project settings

#### 3.8.2 Implementation
```python
class DashboardServer:
    def __init__(self, port=8080):
        self.app = web.Application()
        self.setup_routes()
        self.setup_websocket()
    
    async def index(self, request):
        projects = await self.get_all_projects()
        return web.Response(
            text=self.render_template('dashboard.html', 
                                     projects=projects),
            content_type='text/html'
        )
```

---

## 4. Implementation Roadmap

### Phase 1: Core Foundation (Week 1-2)
- **Objective**: Establish basic project structure and core components
- **Deliverables**:
  - Project scaffolding and repository setup
  - Configuration management system
  - Basic CLI interface
  - Project registration functionality
  - SQLite database schema

### Phase 2: Build System (Week 3)
- **Objective**: Implement build pipeline and process management
- **Deliverables**:
  - Subprocess execution with output streaming
  - Build command execution
  - Environment variable management
  - Error handling and logging
  - Process monitoring

### Phase 3: SSL & Domain Management (Week 4-5)
- **Objective**: Enable HTTPS and custom domain support
- **Deliverables**:
  - Self-signed certificate generation
  - Certificate storage and management
  - Hosts file modification utility
  - Domain-to-project mapping
  - Browser trust instructions

### Phase 4: Reverse Proxy (Week 6-7)
- **Objective**: Implement HTTPS reverse proxy server
- **Deliverables**:
  - aiohttp-based proxy server
  - SSL context configuration
  - Request forwarding logic
  - Header manipulation
  - WebSocket support

### Phase 5: Integration & Polish (Week 8-9)
- **Objective**: Complete system integration and user experience
- **Deliverables**:
  - Complete CLI with all commands
  - Real-time console with rich formatting
  - Comprehensive error handling
  - Documentation and help system
  - Installation scripts

### Phase 6: Testing & Optimization (Week 10)
- **Objective**: Ensure reliability and performance
- **Deliverables**:
  - Unit tests for core components
  - Integration tests
  - Performance optimization
  - Bug fixes
  - User acceptance testing

### Phase 7: Advanced Features (Week 11-12)
- **Objective**: Add optional enhancements
- **Deliverables**:
  - Web dashboard (if time permits)
  - Multiple project support
  - Hot reload functionality
  - Docker integration option
  - Plugin system architecture

---

### Please look at the local-prod-simulator-plan-part-02.md for the rest of the plan.