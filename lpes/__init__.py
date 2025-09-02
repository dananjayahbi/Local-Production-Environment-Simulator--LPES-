"""
LPES - Local Production Environment Simulator

A Python-based development tool designed to replicate production server
environments on local machines for NextJS and web applications.
"""

__version__ = "0.1.0"
__author__ = "LPES Development Team"
__email__ = "dev@lpes.local"

from lpes.core.project_manager import ProjectManager
from lpes.core.config import LPESConfig
from lpes.ssl.manager import SSLManager
from lpes.proxy.server import ProxyServer
from lpes.dns.server import DNSServer

__all__ = [
    "ProjectManager",
    "LPESConfig", 
    "SSLManager",
    "ProxyServer",
    "DNSServer"
]
