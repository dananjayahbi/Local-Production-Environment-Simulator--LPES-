"""
LPES - Local Production Environment Simulator

A comprehensive Python-based development tool designed to replicate production server
environments on local machines for NextJS and web applications with SSL, custom domains,
and production-like features.
"""

__version__ = "1.0.0"
__author__ = "LPES Development Team"
__email__ = "dev@lpes.local"
__description__ = "Local Production Environment Simulator for NextJS and Web Applications"
__license__ = "MIT"
__url__ = "https://github.com/dananjayahbi/Local-Production-Environment-Simulator--LPES-"

# Core functionality
from .core.project_manager import ProjectManager
from .core.config import LPESConfig, ProjectConfig
from .ssl.manager import SSLManager
from .proxy.server import ProxyServer
from .dns.server import DNSServerManager
from .build.monitor import BuildMonitor

__all__ = [
    "ProjectManager",
    "LPESConfig", 
    "ProjectConfig",
    "SSLManager",
    "ProxyServer",
    "DNSServerManager",
    "BuildMonitor",
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    "__license__",
    "__url__"
]
