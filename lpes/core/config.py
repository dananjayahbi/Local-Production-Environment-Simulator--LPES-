"""
Core configuration management for LPES.
Handles project configurations, validation, and persistence.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class DomainConfig(BaseModel):
    """Configuration for a domain."""
    domain: str
    ssl: bool = True
    subdomains: List[str] = Field(default_factory=list)
    aliases: List[str] = Field(default_factory=list)


class BuildConfig(BaseModel):
    """Build configuration for a project."""
    command: str
    env: Dict[str, str] = Field(default_factory=dict)
    pre_build: List[str] = Field(default_factory=list)
    post_build: List[str] = Field(default_factory=list)
    timeout: int = 300  # 5 minutes default


class StartConfig(BaseModel):
    """Start configuration for a project."""
    command: str
    port: int = 3000
    env: Dict[str, str] = Field(default_factory=dict)
    health_check: Optional[Dict[str, Any]] = None


class SSLConfig(BaseModel):
    """SSL configuration."""
    auto_generate: bool = True
    cert_path: Optional[str] = None
    key_path: Optional[str] = None
    ca_path: Optional[str] = None


class NextJSConfig(BaseModel):
    """NextJS specific configuration."""
    images: Optional[Dict[str, Any]] = None
    headers: Optional[List[Dict[str, Any]]] = None


class ProjectConfig(BaseModel):
    """Complete project configuration."""
    name: str
    type: str = "nextjs"
    path: str
    build: BuildConfig
    start: StartConfig
    domains: List[DomainConfig] = Field(default_factory=list)
    ssl: SSLConfig = Field(default_factory=SSLConfig)
    next_config: Optional[NextJSConfig] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @validator('path')
    def validate_path(cls, v):
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Project path does not exist: {v}")
        if not path.is_dir():
            raise ValueError(f"Project path is not a directory: {v}")
        return str(path.absolute())

    @validator('domains')
    def validate_domains(cls, v):
        # Allow empty domains during project creation, can be added later
        return v


class GlobalConfig(BaseModel):
    """Global LPES configuration."""
    ssl: Dict[str, Any] = Field(default_factory=lambda: {
        "ca_path": "~/.lpes/ca",
        "cert_store": "~/.lpes/certificates"
    })
    proxy: Dict[str, Any] = Field(default_factory=lambda: {
        "port": 443,
        "fallback_port": 8443
    })
    dns: Dict[str, Any] = Field(default_factory=lambda: {
        "enabled": True,
        "port": 53,
        "cache_ttl": 300
    })
    data_dir: str = Field(default="~/.lpes")
    log_level: str = "INFO"


class LPESConfig:
    """Main configuration manager for LPES."""
    
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "~/.lpes").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.data_dir / "config.yaml"
        self.projects_dir = self.data_dir / "projects"
        self.ssl_dir = self.data_dir / "ssl"
        self.ca_dir = self.data_dir / "ca"
        
        # Create subdirectories
        for dir_path in [self.projects_dir, self.ssl_dir, self.ca_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self._global_config = self._load_global_config()
    
    def _load_global_config(self) -> GlobalConfig:
        """Load global configuration from file."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            return GlobalConfig(**data)
        else:
            config = GlobalConfig()
            self._save_global_config(config)
            return config
    
    def _save_global_config(self, config: GlobalConfig):
        """Save global configuration to file."""
        with open(self.config_file, 'w') as f:
            yaml.dump(config.dict(), f, default_flow_style=False)
    
    @property
    def global_config(self) -> GlobalConfig:
        """Get global configuration."""
        return self._global_config
    
    def get_project_config_path(self, project_name: str) -> Path:
        """Get path for project configuration file."""
        return self.projects_dir / f"{project_name}.yaml"
    
    def load_project_config(self, project_name: str) -> Optional[ProjectConfig]:
        """Load project configuration."""
        config_path = self.get_project_config_path(project_name)
        if not config_path.exists():
            return None
        
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        return ProjectConfig(**data)
    
    def save_project_config(self, config: ProjectConfig):
        """Save project configuration."""
        config.updated_at = datetime.now()
        config_path = self.get_project_config_path(config.name)
        
        with open(config_path, 'w') as f:
            yaml.dump(config.dict(), f, default_flow_style=False)
    
    def delete_project_config(self, project_name: str) -> bool:
        """Delete project configuration."""
        config_path = self.get_project_config_path(project_name)
        if config_path.exists():
            config_path.unlink()
            return True
        return False
    
    def list_projects(self) -> List[str]:
        """List all configured projects."""
        projects = []
        for config_file in self.projects_dir.glob("*.yaml"):
            projects.append(config_file.stem)
        return sorted(projects)
    
    def project_exists(self, project_name: str) -> bool:
        """Check if project configuration exists."""
        return self.get_project_config_path(project_name).exists()
    
    def get_ssl_cert_path(self, domain: str) -> Path:
        """Get SSL certificate path for domain."""
        return self.ssl_dir / f"{domain}.crt"
    
    def get_ssl_key_path(self, domain: str) -> Path:
        """Get SSL private key path for domain."""
        return self.ssl_dir / f"{domain}.key"
    
    def get_ca_cert_path(self) -> Path:
        """Get CA certificate path."""
        return self.ca_dir / "ca.crt"
    
    def get_ca_key_path(self) -> Path:
        """Get CA private key path."""
        return self.ca_dir / "ca.key"
