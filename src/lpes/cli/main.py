"""
Command Line Interface for LPES.
Provides comprehensive CLI commands for managing projects, domains, and services.
"""

import asyncio
import click
import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.text import Text

from lpes.core.config import LPESConfig, ProjectConfig, BuildConfig, StartConfig, DomainConfig
from lpes.core.project_manager import ProjectManager
from lpes.ssl.manager import SSLManager
from lpes.proxy.server import ProxyServer
from lpes.dns.server import DNSServerManager, HostsFileManager
from lpes.build.monitor import BuildMonitor


console = Console()
logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


class LPESContext:
    """CLI context object."""
    
    def __init__(self):
        self.config = LPESConfig()
        self.project_manager = ProjectManager(self.config)
        self.ssl_manager = SSLManager(self.config)
        self.build_monitor = BuildMonitor(self.config)
        self.proxy_server = ProxyServer(self.config, self.project_manager, self.ssl_manager)
        self.dns_manager = DNSServerManager(self.config)
        self.hosts_manager = HostsFileManager()


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--data-dir', help='LPES data directory')
@click.pass_context
def cli(ctx, verbose, data_dir):
    """LPES - Local Production Environment Simulator"""
    setup_logging("DEBUG" if verbose else "INFO")
    
    # Initialize context
    if data_dir:
        lpes_context = LPESContext()
        lpes_context.config = LPESConfig(data_dir)
        lpes_context.project_manager = ProjectManager(lpes_context.config)
        lpes_context.ssl_manager = SSLManager(lpes_context.config)
        lpes_context.build_monitor = BuildMonitor(lpes_context.config)
        lpes_context.proxy_server = ProxyServer(
            lpes_context.config, 
            lpes_context.project_manager, 
            lpes_context.ssl_manager
        )
        lpes_context.dns_manager = DNSServerManager(lpes_context.config)
        lpes_context.hosts_manager = HostsFileManager()
    else:
        lpes_context = LPESContext()
    
    ctx.obj = lpes_context


@cli.command()
@click.option('--path', required=True, help='Project root path')
@click.option('--build', required=True, help='Build command')
@click.option('--start', required=True, help='Start command')
@click.option('--port', default=3000, help='Development server port')
@click.option('--type', 'project_type', default='nextjs', help='Project type')
@click.argument('name')
@click.pass_obj
def init(ctx: LPESContext, path, build, start, port, project_type, name):
    """Initialize a new project"""
    try:
        with console.status(f"[bold green]Initializing project {name}..."):
            project = ctx.project_manager.create_project(
                name=name,
                path=path,
                build_command=build,
                start_command=start,
                port=port,
                project_type=project_type
            )
        
        console.print(f"✅ Project [bold cyan]{name}[/bold cyan] initialized successfully!")
        console.print(f"📁 Path: {project.config.path}")
        console.print(f"🔨 Build: {project.config.build.command}")
        console.print(f"🚀 Start: {project.config.start.command}")
        console.print(f"🌐 Port: {project.config.start.port}")
        
        console.print("\n📝 Next steps:")
        console.print(f"  1. Add a domain: [bold]lpes domain add {name} <domain>[/bold]")
        console.print(f"  2. Build project: [bold]lpes build {name}[/bold]")
        console.print(f"  3. Start project: [bold]lpes start {name}[/bold]")
        
    except Exception as e:
        console.print(f"❌ Failed to initialize project: {e}", style="bold red")
        sys.exit(1)


@cli.command()
@click.pass_obj
def list(ctx: LPESContext):
    """List all projects"""
    projects = ctx.project_manager.list_projects()
    
    if not projects:
        console.print("No projects found. Initialize a project with [bold]lpes init[/bold]")
        return
    
    table = Table(title="LPES Projects")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Domain", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Port", justify="center")
    table.add_column("Type", style="dim")
    
    for project in projects:
        status = "🟢 Running" if project.is_running else "🔴 Stopped"
        if project.is_building:
            status = "🟡 Building"
        
        primary_domain = project.get_primary_domain() or "Not configured"
        
        table.add_row(
            project.name,
            primary_domain,
            status,
            str(project.config.start.port),
            project.config.type
        )
    
    console.print(table)


@cli.command()
@click.argument('project_name')
@click.option('--force', is_flag=True, help='Force rebuild (skip cache)')
@click.pass_obj
def build(ctx: LPESContext, project_name, force):
    """Build a project"""
    project = ctx.project_manager.get_project(project_name)
    if not project:
        console.print(f"❌ Project '{project_name}' not found", style="bold red")
        sys.exit(1)
    
    console.print(f"🔨 Building project [bold cyan]{project_name}[/bold cyan]...")
    
    # Progress tracking
    build_output = []
    
    def on_output(line):
        console.print(f"[dim]│[/dim] {line}")
        build_output.append(line)
    
    def on_error(line):
        console.print(f"[dim]│[/dim] [red]{line}[/red]")
        build_output.append(line)
    
    async def run_build():
        session = await ctx.build_monitor.execute_build(
            project.config,
            on_output=on_output,
            on_error=on_error,
            force_rebuild=force
        )
        return session
    
    # Run build
    session = asyncio.run(run_build())
    
    if session.success:
        console.print(f"✅ Build completed successfully in {session.duration:.2f}s")
    else:
        console.print(f"❌ Build failed: {session.error_message}", style="bold red")
        sys.exit(1)


@cli.command()
@click.argument('project_name')
@click.option('--build-first', is_flag=True, help='Build before starting')
@click.pass_obj
def start(ctx: LPESContext, project_name, build_first):
    """Start a project"""
    project = ctx.project_manager.get_project(project_name)
    if not project:
        console.print(f"❌ Project '{project_name}' not found", style="bold red")
        sys.exit(1)
    
    async def run_start():
        # Build first if requested
        if build_first:
            console.print("🔨 Building project first...")
            session = await ctx.build_monitor.execute_build(project.config)
            if not session.success:
                console.print(f"❌ Build failed: {session.error_message}", style="bold red")
                return False
        
        # Start project
        console.print(f"🚀 Starting project [bold cyan]{project_name}[/bold cyan]...")
        
        def on_output(line):
            console.print(f"[dim]│[/dim] {line}")
        
        def on_error(line):
            console.print(f"[dim]│[/dim] [red]{line}[/red]")
        
        success = await project.start(on_output=on_output, on_error=on_error)
        
        if success:
            primary_domain = project.get_primary_domain()
            console.print(f"✅ Project [bold cyan]{project_name}[/bold cyan] started successfully!")
            console.print(f"🌐 Local server: http://localhost:{project.config.start.port}")
            if primary_domain:
                console.print(f"🔒 HTTPS domain: https://{primary_domain}")
            console.print("\n💡 Use [bold]lpes proxy start[/bold] to enable HTTPS access")
        else:
            console.print(f"❌ Failed to start project {project_name}", style="bold red")
            return False
        
        return True
    
    success = asyncio.run(run_start())
    if not success:
        sys.exit(1)


@cli.command()
@click.argument('project_name')
@click.pass_obj
def stop(ctx: LPESContext, project_name):
    """Stop a project"""
    project = ctx.project_manager.get_project(project_name)
    if not project:
        console.print(f"❌ Project '{project_name}' not found", style="bold red")
        sys.exit(1)
    
    async def run_stop():
        console.print(f"⏹️  Stopping project [bold cyan]{project_name}[/bold cyan]...")
        success = await project.stop()
        return success
    
    success = asyncio.run(run_stop())
    
    if success:
        console.print(f"✅ Project [bold cyan]{project_name}[/bold cyan] stopped")
    else:
        console.print(f"❌ Failed to stop project {project_name}", style="bold red")
        sys.exit(1)


@cli.command()
@click.argument('project_name')
@click.pass_obj
def restart(ctx: LPESContext, project_name):
    """Restart a project"""
    project = ctx.project_manager.get_project(project_name)
    if not project:
        console.print(f"❌ Project '{project_name}' not found", style="bold red")
        sys.exit(1)
    
    async def run_restart():
        console.print(f"🔄 Restarting project [bold cyan]{project_name}[/bold cyan]...")
        
        def on_output(line):
            console.print(f"[dim]│[/dim] {line}")
        
        def on_error(line):
            console.print(f"[dim]│[/dim] [red]{line}[/red]")
        
        success = await project.restart(on_output=on_output, on_error=on_error)
        return success
    
    success = asyncio.run(run_restart())
    
    if success:
        console.print(f"✅ Project [bold cyan]{project_name}[/bold cyan] restarted successfully")
    else:
        console.print(f"❌ Failed to restart project {project_name}", style="bold red")
        sys.exit(1)


@cli.command()
@click.argument('project_name')
@click.option('--cleanup', is_flag=True, help='Clean up SSL certificates and domains')
@click.pass_obj
def remove(ctx: LPESContext, project_name, cleanup):
    """Remove a project"""
    project = ctx.project_manager.get_project(project_name)
    if not project:
        console.print(f"❌ Project '{project_name}' not found", style="bold red")
        sys.exit(1)
    
    # Confirm removal
    if not click.confirm(f"Are you sure you want to remove project '{project_name}'?"):
        console.print("Cancelled")
        return
    
    # Clean up domains and SSL if requested
    if cleanup:
        domains = project.get_all_domains()
        for domain in domains:
            ctx.ssl_manager.revoke_certificate(domain)
            ctx.hosts_manager.remove_domain(domain)
        console.print(f"🧹 Cleaned up {len(domains)} domains")
    
    # Remove project
    success = ctx.project_manager.remove_project(project_name)
    
    if success:
        console.print(f"✅ Project [bold cyan]{project_name}[/bold cyan] removed")
    else:
        console.print(f"❌ Failed to remove project {project_name}", style="bold red")
        sys.exit(1)


# Domain management commands
@cli.group()
def domain():
    """Domain management commands"""
    pass


@domain.command('add')
@click.argument('project_name')
@click.argument('domain_name')
@click.option('--ssl/--no-ssl', default=True, help='Enable SSL for domain')
@click.option('--primary', is_flag=True, help='Set as primary domain')
@click.option('--hosts-file', is_flag=True, help='Add to system hosts file')
@click.pass_obj
def add_domain(ctx: LPESContext, project_name, domain_name, ssl, primary, hosts_file):
    """Add a domain to a project"""
    success = ctx.project_manager.add_domain_to_project(
        project_name, domain_name, ssl, primary
    )
    
    if not success:
        console.print(f"❌ Failed to add domain {domain_name}", style="bold red")
        sys.exit(1)
    
    # Generate SSL certificate
    if ssl:
        with console.status("🔒 Generating SSL certificate..."):
            ctx.ssl_manager.generate_certificate(domain_name)
        console.print(f"🔒 SSL certificate generated for {domain_name}")
    
    # Add to hosts file
    if hosts_file:
        with console.status("📝 Adding to hosts file..."):
            success = ctx.hosts_manager.add_domain(domain_name)
            if success:
                console.print(f"📝 Added {domain_name} to hosts file")
            else:
                console.print(f"⚠️  Failed to add {domain_name} to hosts file (may need admin privileges)", style="yellow")
    
    console.print(f"✅ Domain [bold cyan]{domain_name}[/bold cyan] added to project [bold cyan]{project_name}[/bold cyan]")


@domain.command('list')
@click.argument('project_name', required=False)
@click.pass_obj
def list_domains(ctx: LPESContext, project_name):
    """List domains for a project or all projects"""
    if project_name:
        project = ctx.project_manager.get_project(project_name)
        if not project:
            console.print(f"❌ Project '{project_name}' not found", style="bold red")
            sys.exit(1)
        projects = [project]
    else:
        projects = ctx.project_manager.list_projects()
    
    table = Table(title="Project Domains")
    table.add_column("Project", style="cyan")
    table.add_column("Domain", style="magenta")
    table.add_column("SSL", justify="center")
    table.add_column("Status", justify="center")
    
    for project in projects:
        for domain_config in project.config.domains:
            ssl_status = "🔒 Yes" if domain_config.ssl else "❌ No"
            
            # Check if certificate exists
            cert_path = ctx.ssl_manager.config.get_ssl_cert_path(domain_config.domain)
            cert_status = "✅ Valid" if cert_path.exists() else "❌ Missing"
            
            table.add_row(
                project.name,
                domain_config.domain,
                ssl_status,
                cert_status
            )
    
    console.print(table)


# Proxy server commands
@cli.group()
def proxy():
    """Proxy server management"""
    pass


@proxy.command('start')
@click.option('--port', default=443, help='HTTPS port')
@click.option('--fallback-port', default=8443, help='Fallback port if primary fails')
@click.pass_obj
def start_proxy(ctx: LPESContext, port, fallback_port):
    """Start the HTTPS proxy server"""
    async def run_proxy():
        console.print(f"🔒 Starting HTTPS proxy on port {port}...")
        success = await ctx.proxy_server.start(port, fallback_port)
        
        if success:
            console.print(f"✅ HTTPS proxy server running")
            
            # List available domains
            projects = ctx.project_manager.list_projects()
            running_projects = [p for p in projects if p.is_running]
            
            if running_projects:
                console.print("\n🌐 Available domains:")
                for project in running_projects:
                    for domain in project.get_all_domains():
                        console.print(f"  • https://{domain}")
            else:
                console.print("\n💡 Start a project to access domains via HTTPS")
            
            # Keep server running
            try:
                while ctx.proxy_server.is_running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                console.print("\n⏹️  Stopping proxy server...")
                await ctx.proxy_server.stop()
        else:
            console.print("❌ Failed to start proxy server", style="bold red")
            return False
        
        return True
    
    success = asyncio.run(run_proxy())
    if not success:
        sys.exit(1)


@proxy.command('stop')
@click.pass_obj
def stop_proxy(ctx: LPESContext):
    """Stop the HTTPS proxy server"""
    async def run_stop():
        success = await ctx.proxy_server.stop()
        return success
    
    success = asyncio.run(run_stop())
    
    if success:
        console.print("✅ Proxy server stopped")
    else:
        console.print("❌ Failed to stop proxy server", style="bold red")
        sys.exit(1)


# SSL certificate commands
@cli.group()
def ssl():
    """SSL certificate management"""
    pass


@ssl.command('list')
@click.pass_obj
def list_certificates(ctx: LPESContext):
    """List SSL certificates"""
    certificates = ctx.ssl_manager.list_certificates()
    
    if not certificates:
        console.print("No SSL certificates found")
        return
    
    table = Table(title="SSL Certificates")
    table.add_column("Domain", style="cyan")
    table.add_column("Expires", style="magenta")
    table.add_column("Status", justify="center")
    
    for domain, expiration, is_valid in certificates:
        status = "✅ Valid" if is_valid else "❌ Expired"
        table.add_row(domain, expiration.strftime("%Y-%m-%d %H:%M"), status)
    
    console.print(table)


@ssl.command('generate')
@click.argument('domain')
@click.pass_obj
def generate_certificate(ctx: LPESContext, domain):
    """Generate SSL certificate for a domain"""
    with console.status(f"🔒 Generating SSL certificate for {domain}..."):
        cert_path, key_path = ctx.ssl_manager.generate_certificate(domain)
    
    console.print(f"✅ SSL certificate generated for [bold cyan]{domain}[/bold cyan]")
    console.print(f"📄 Certificate: {cert_path}")
    console.print(f"🔑 Private key: {key_path}")


@ssl.command('trust-info')
@click.pass_obj
def trust_info(ctx: LPESContext):
    """Show instructions for trusting the CA certificate"""
    instructions = ctx.ssl_manager.get_trust_instructions()
    console.print(Panel(instructions, title="🔒 CA Certificate Trust Instructions", border_style="blue"))


if __name__ == '__main__':
    cli()
