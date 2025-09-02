"""
DNS server implementation for LPES.
Handles local DNS resolution for custom domains.
"""

import asyncio
import logging
import socket
from typing import Dict, Set, Optional, Tuple, List
from pathlib import Path
import platform

try:
    from dnslib import DNSRecord, RR, QTYPE, A, AAAA
    from dnslib.server import DNSServer, BaseResolver
    DNS_AVAILABLE = True
except ImportError:
    # Fallback when dnslib is not available
    DNS_AVAILABLE = False
    DNSRecord = None
    RR = None
    QTYPE = None
    A = None
    AAAA = None
    DNSServer = None
    BaseResolver = object

from lpes.core.config import LPESConfig


logger = logging.getLogger(__name__)


class LPESResolver(BaseResolver):
    """Custom DNS resolver for LPES domains."""
    
    def __init__(self, config: LPESConfig):
        self.config = config
        self.managed_domains: Set[str] = set()
        self.domain_mappings: Dict[str, str] = {}  # domain -> ip
        self.upstream_dns = self._get_system_dns()
        
    def _get_system_dns(self) -> str:
        """Get system DNS server."""
        try:
            # Try to get DNS from system configuration
            if platform.system() == "Windows":
                import subprocess
                result = subprocess.run(
                    ["nslookup", "google.com"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                # Parse output to find DNS server
                for line in result.stdout.split('\n'):
                    if 'Server:' in line:
                        dns_server = line.split(':')[1].strip()
                        if dns_server and dns_server != '127.0.0.1':
                            return dns_server
            else:
                # Linux/macOS
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if line.startswith('nameserver'):
                            dns_server = line.split()[1]
                            if dns_server != '127.0.0.1':
                                return dns_server
        except Exception as e:
            logger.warning(f"Failed to get system DNS: {e}")
        
        # Fallback to common public DNS
        return "8.8.8.8"
    
    def add_domain(self, domain: str, ip: str = "127.0.0.1"):
        """Add a domain to be resolved to the specified IP."""
        self.managed_domains.add(domain)
        self.domain_mappings[domain] = ip
        logger.info(f"Added DNS mapping: {domain} -> {ip}")
    
    def remove_domain(self, domain: str):
        """Remove a domain from management."""
        self.managed_domains.discard(domain)
        self.domain_mappings.pop(domain, None)
        logger.info(f"Removed DNS mapping for {domain}")
    
    def is_managed_domain(self, domain: str) -> bool:
        """Check if a domain is managed by LPES."""
        # Check exact match
        if domain in self.managed_domains:
            return True
        
        # Check wildcard subdomains
        parts = domain.split('.')
        if len(parts) > 1:
            parent_domain = '.'.join(parts[1:])
            if parent_domain in self.managed_domains:
                return True
        
        return False
    
    def resolve(self, request, handler):
        """Resolve DNS request."""
        reply = request.reply()
        qname = str(request.q.qname).rstrip('.')
        qtype = request.q.qtype
        
        logger.debug(f"DNS query: {qname} ({QTYPE[qtype]})")
        
        # Handle managed domains
        if self.is_managed_domain(qname):
            ip = self._get_ip_for_domain(qname)
            
            if qtype == QTYPE.A:
                # IPv4 address
                reply.add_answer(RR(qname, QTYPE.A, rdata=A(ip), ttl=300))
                logger.debug(f"Resolved {qname} to {ip}")
                return reply
            elif qtype == QTYPE.AAAA:
                # IPv6 - return empty response
                return reply
        
        # Forward to upstream DNS for non-managed domains
        try:
            upstream_response = self._query_upstream(request)
            if upstream_response:
                return upstream_response
        except Exception as e:
            logger.warning(f"Upstream DNS query failed: {e}")
        
        # Return empty response if all else fails
        return reply
    
    def _get_ip_for_domain(self, domain: str) -> str:
        """Get IP address for a domain."""
        # Check direct mapping
        if domain in self.domain_mappings:
            return self.domain_mappings[domain]
        
        # Check parent domain for wildcard
        parts = domain.split('.')
        if len(parts) > 1:
            parent_domain = '.'.join(parts[1:])
            if parent_domain in self.domain_mappings:
                return self.domain_mappings[parent_domain]
        
        # Default to localhost
        return "127.0.0.1"
    
    def _query_upstream(self, request):
        """Query upstream DNS server."""
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            
            # Send query
            query_data = request.pack()
            sock.sendto(query_data, (self.upstream_dns, 53))
            
            # Receive response
            response_data, _ = sock.recvfrom(1024)
            response = DNSRecord.parse(response_data)
            
            sock.close()
            return response
            
        except Exception as e:
            logger.warning(f"Upstream DNS query failed: {e}")
            return None


class DNSServerManager:
    """Manages the LPES DNS server."""
    
    def __init__(self, config: Optional[LPESConfig] = None):
        self.config = config or LPESConfig()
        self.resolver = LPESResolver(self.config)
        self.server: Optional[DNSServer] = None
        self.is_running = False
        self._server_task: Optional[asyncio.Task] = None
    
    async def start(self, port: int = 5353) -> bool:
        """Start the DNS server."""
        if self.is_running:
            logger.warning("DNS server is already running")
            return True
        
        try:
            # Use alternative port if we can't bind to 53
            actual_port = port if port != 53 else 5353
            
            logger.info(f"Starting DNS server on port {actual_port}")
            
            # Create and start DNS server
            self.server = DNSServer(
                self.resolver,
                port=actual_port,
                address="127.0.0.1",
                tcp=False  # UDP only for now
            )
            
            # Start server in background
            self._server_task = asyncio.create_task(self._run_server())
            
            self.is_running = True
            logger.info(f"DNS server started on 127.0.0.1:{actual_port}")
            
            if actual_port != 53:
                logger.warning(
                    f"DNS server running on port {actual_port} instead of 53. "
                    "You may need to configure your system to use 127.0.0.1:{actual_port} as DNS server."
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start DNS server: {e}")
            self.is_running = False
            return False
    
    async def stop(self) -> bool:
        """Stop the DNS server."""
        if not self.is_running:
            logger.warning("DNS server is not running")
            return True
        
        try:
            logger.info("Stopping DNS server")
            
            if self._server_task:
                self._server_task.cancel()
                try:
                    await self._server_task
                except asyncio.CancelledError:
                    pass
            
            if self.server:
                self.server.stop()
            
            self.is_running = False
            self._server_task = None
            
            logger.info("DNS server stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop DNS server: {e}")
            return False
    
    async def _run_server(self):
        """Run the DNS server."""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self.server.start_thread
            )
        except Exception as e:
            logger.error(f"DNS server error: {e}")
            self.is_running = False
    
    def add_domain(self, domain: str, ip: str = "127.0.0.1"):
        """Add a domain to be resolved by the DNS server."""
        self.resolver.add_domain(domain, ip)
    
    def remove_domain(self, domain: str):
        """Remove a domain from the DNS server."""
        self.resolver.remove_domain(domain)
    
    def list_domains(self) -> Dict[str, str]:
        """List all managed domains and their IP mappings."""
        return self.resolver.domain_mappings.copy()


class HostsFileManager:
    """Alternative to DNS server - manages system hosts file."""
    
    def __init__(self):
        self.hosts_file_path = self._get_hosts_file_path()
        self.backup_path = Path.home() / ".lpes" / "hosts.backup"
        self.lpes_marker = "# LPES managed domains"
        
    def _get_hosts_file_path(self) -> Path:
        """Get the system hosts file path."""
        if platform.system() == "Windows":
            return Path("C:/Windows/System32/drivers/etc/hosts")
        else:
            return Path("/etc/hosts")
    
    def _backup_hosts_file(self):
        """Create a backup of the original hosts file."""
        if not self.backup_path.parent.exists():
            self.backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.backup_path.exists():
            try:
                import shutil
                shutil.copy2(self.hosts_file_path, self.backup_path)
                logger.info(f"Created hosts file backup: {self.backup_path}")
            except Exception as e:
                logger.warning(f"Failed to create hosts file backup: {e}")
    
    def add_domain(self, domain: str, ip: str = "127.0.0.1") -> bool:
        """Add a domain to the hosts file."""
        try:
            self._backup_hosts_file()
            
            # Read current hosts file
            with open(self.hosts_file_path, 'r') as f:
                lines = f.readlines()
            
            # Check if already exists
            domain_line = f"{ip} {domain}\n"
            if domain_line in lines:
                logger.info(f"Domain {domain} already exists in hosts file")
                return True
            
            # Find or create LPES section
            lpes_start = -1
            lpes_end = -1
            
            for i, line in enumerate(lines):
                if self.lpes_marker in line:
                    lpes_start = i
                elif lpes_start != -1 and line.strip() == "":
                    lpes_end = i
                    break
            
            # Add domain
            if lpes_start == -1:
                # Create new LPES section
                lines.append(f"\n{self.lpes_marker}\n")
                lines.append(domain_line)
            else:
                # Add to existing section
                if lpes_end == -1:
                    lpes_end = len(lines)
                lines.insert(lpes_end, domain_line)
            
            # Write updated hosts file
            with open(self.hosts_file_path, 'w') as f:
                f.writelines(lines)
            
            logger.info(f"Added {domain} to hosts file")
            return True
            
        except PermissionError:
            logger.error(
                f"Permission denied: Cannot modify hosts file {self.hosts_file_path}. "
                "Run as administrator/sudo."
            )
            return False
        except Exception as e:
            logger.error(f"Failed to add domain to hosts file: {e}")
            return False
    
    def remove_domain(self, domain: str) -> bool:
        """Remove a domain from the hosts file."""
        try:
            # Read current hosts file
            with open(self.hosts_file_path, 'r') as f:
                lines = f.readlines()
            
            # Remove domain lines
            updated_lines = []
            removed = False
            
            for line in lines:
                if line.strip().endswith(domain) and not line.strip().startswith('#'):
                    removed = True
                    logger.info(f"Removing hosts entry: {line.strip()}")
                else:
                    updated_lines.append(line)
            
            if removed:
                # Write updated hosts file
                with open(self.hosts_file_path, 'w') as f:
                    f.writelines(updated_lines)
                logger.info(f"Removed {domain} from hosts file")
            else:
                logger.warning(f"Domain {domain} not found in hosts file")
            
            return removed
            
        except PermissionError:
            logger.error(
                f"Permission denied: Cannot modify hosts file {self.hosts_file_path}. "
                "Run as administrator/sudo."
            )
            return False
        except Exception as e:
            logger.error(f"Failed to remove domain from hosts file: {e}")
            return False
    
    def list_lpes_domains(self) -> List[Tuple[str, str]]:
        """List all LPES-managed domains in the hosts file."""
        domains = []
        
        try:
            with open(self.hosts_file_path, 'r') as f:
                lines = f.readlines()
            
            in_lpes_section = False
            for line in lines:
                if self.lpes_marker in line:
                    in_lpes_section = True
                    continue
                elif in_lpes_section and line.strip() == "":
                    break
                elif in_lpes_section and not line.strip().startswith('#'):
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        ip, domain = parts[0], parts[1]
                        domains.append((domain, ip))
                        
        except Exception as e:
            logger.error(f"Failed to read hosts file: {e}")
        
        return domains
    
    def cleanup_all_domains(self) -> bool:
        """Remove all LPES-managed domains from hosts file."""
        try:
            # Read current hosts file
            with open(self.hosts_file_path, 'r') as f:
                lines = f.readlines()
            
            # Remove LPES section
            updated_lines = []
            in_lpes_section = False
            removed_count = 0
            
            for line in lines:
                if self.lpes_marker in line:
                    in_lpes_section = True
                    continue
                elif in_lpes_section and line.strip() == "":
                    in_lpes_section = False
                    updated_lines.append(line)  # Keep the empty line
                elif not in_lpes_section:
                    updated_lines.append(line)
                else:
                    # Skip lines in LPES section
                    removed_count += 1
            
            if removed_count > 0:
                # Write updated hosts file
                with open(self.hosts_file_path, 'w') as f:
                    f.writelines(updated_lines)
                logger.info(f"Removed {removed_count} LPES domains from hosts file")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup hosts file: {e}")
            return False
    
    def restore_backup(self) -> bool:
        """Restore hosts file from backup."""
        try:
            if self.backup_path.exists():
                import shutil
                shutil.copy2(self.backup_path, self.hosts_file_path)
                logger.info("Restored hosts file from backup")
                return True
            else:
                logger.warning("No hosts file backup found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to restore hosts file backup: {e}")
            return False
