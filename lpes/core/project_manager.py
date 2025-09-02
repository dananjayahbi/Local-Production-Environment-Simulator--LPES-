"""
Project management functionality for LPES.
Handles project creation, registration, and lifecycle management.
"""

import asyncio
import logging
import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from lpes.core.config import (
    LPESConfig, ProjectConfig, BuildConfig, StartConfig, 
    DomainConfig, SSLConfig
)


logger = logging.getLogger(__name__)


class Project:
    """Represents a project managed by LPES."""
    
    def __init__(self, config: ProjectConfig, lpes_config: LPESConfig):
        self.config = config
        self.lpes_config = lpes_config
        self._process: Optional[asyncio.subprocess.Process] = None
        self._is_running = False
        self._build_in_progress = False
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def path(self) -> Path:
        return Path(self.config.path)
    
    @property
    def is_running(self) -> bool:
        return self._is_running and self._process is not None
    
    @property
    def is_building(self) -> bool:
        return self._build_in_progress
    
    def get_primary_domain(self) -> Optional[str]:
        """Get the primary domain for this project."""
        if self.config.domains:
            return self.config.domains[0].domain
        return None
    
    def get_all_domains(self) -> List[str]:
        """Get all domains (including subdomains and aliases) for this project."""
        domains = []
        for domain_config in self.config.domains:
            domains.append(domain_config.domain)
            domains.extend(domain_config.aliases)
            for subdomain in domain_config.subdomains:
                domains.append(f"{subdomain}.{domain_config.domain}")
        return domains
    
    async def build(self, on_output=None, on_error=None) -> bool:
        """Build the project."""
        if self._build_in_progress:
            logger.warning(f"Build already in progress for project {self.name}")
            return False
        
        self._build_in_progress = True
        logger.info(f"Starting build for project {self.name}")
        
        try:
            # Run pre-build commands
            for cmd in self.config.build.pre_build:
                success = await self._run_command(
                    cmd, 
                    on_output=on_output, 
                    on_error=on_error,
                    timeout=60
                )
                if not success:
                    logger.error(f"Pre-build command failed: {cmd}")
                    return False
            
            # Run main build command
            success = await self._run_command(
                self.config.build.command,
                env=self.config.build.env,
                on_output=on_output,
                on_error=on_error,
                timeout=self.config.build.timeout
            )
            
            if success:
                # Run post-build commands
                for cmd in self.config.build.post_build:
                    await self._run_command(
                        cmd,
                        on_output=on_output,
                        on_error=on_error,
                        timeout=60
                    )
                logger.info(f"Build completed successfully for project {self.name}")
            else:
                logger.error(f"Build failed for project {self.name}")
            
            return success
            
        finally:
            self._build_in_progress = False
    
    async def start(self, on_output=None, on_error=None) -> bool:
        """Start the project server."""
        if self.is_running:
            logger.warning(f"Project {self.name} is already running")
            return True
        
        logger.info(f"Starting project {self.name}")
        
        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(self.config.start.env)
            
            # Start the process
            self._process = await asyncio.create_subprocess_shell(
                self.config.start.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.config.path,
                env=env
            )
            
            self._is_running = True
            
            # Start log monitoring
            if on_output or on_error:
                asyncio.create_task(self._monitor_process(on_output, on_error))
            
            logger.info(f"Project {self.name} started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start project {self.name}: {e}")
            self._is_running = False
            return False
    
    async def stop(self) -> bool:
        """Stop the project server."""
        if not self.is_running:
            logger.warning(f"Project {self.name} is not running")
            return True
        
        logger.info(f"Stopping project {self.name}")
        
        try:
            if self._process:
                self._process.terminate()
                try:
                    await asyncio.wait_for(self._process.wait(), timeout=10)
                except asyncio.TimeoutError:
                    logger.warning(f"Force killing project {self.name}")
                    self._process.kill()
                    await self._process.wait()
                
                # Properly close the process to avoid warnings
                if hasattr(self._process, 'stdout') and self._process.stdout:
                    self._process.stdout.close()
                if hasattr(self._process, 'stderr') and self._process.stderr:
                    self._process.stderr.close()
            
            self._is_running = False
            self._process = None
            logger.info(f"Project {self.name} stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop project {self.name}: {e}")
            return False
    
    async def restart(self, on_output=None, on_error=None) -> bool:
        """Restart the project server."""
        logger.info(f"Restarting project {self.name}")
        await self.stop()
        return await self.start(on_output, on_error)
    
    async def _run_command(self, command: str, env=None, on_output=None, 
                          on_error=None, timeout=300) -> bool:
        """Run a shell command."""
        try:
            cmd_env = os.environ.copy()
            if env:
                cmd_env.update(env)
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.config.path,
                env=cmd_env
            )
            
            # Monitor output
            if on_output or on_error:
                asyncio.create_task(
                    self._stream_process_output(process, on_output, on_error)
                )
            
            # Wait for completion
            try:
                await asyncio.wait_for(process.wait(), timeout=timeout)
                return process.returncode == 0
            except asyncio.TimeoutError:
                logger.error(f"Command timeout: {command}")
                process.kill()
                return False
                
        except Exception as e:
            logger.error(f"Command execution failed: {command}, error: {e}")
            return False
    
    async def _monitor_process(self, on_output=None, on_error=None):
        """Monitor running process output."""
        if self._process:
            await self._stream_process_output(self._process, on_output, on_error)
    
    async def _stream_process_output(self, process, on_output=None, on_error=None):
        """Stream process output to callbacks."""
        async def read_stream(stream, callback):
            while True:
                line = await stream.readline()
                if not line:
                    break
                if callback:
                    callback(line.decode().strip())
        
        if process.stdout and on_output:
            asyncio.create_task(read_stream(process.stdout, on_output))
        
        if process.stderr and on_error:
            asyncio.create_task(read_stream(process.stderr, on_error))


class ProjectManager:
    """Manages LPES projects."""
    
    def __init__(self, config: Optional[LPESConfig] = None):
        self.config = config or LPESConfig()
        self._projects: Dict[str, Project] = {}
        self._init_database()
        self._load_projects()
    
    def _init_database(self):
        """Initialize SQLite database for project metadata."""
        db_path = self.config.data_dir / "projects.db"
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                name TEXT PRIMARY KEY,
                path TEXT NOT NULL,
                type TEXT NOT NULL,
                status TEXT DEFAULT 'stopped',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS domains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                domain TEXT NOT NULL,
                is_primary BOOLEAN DEFAULT FALSE,
                ssl_enabled BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (project_name) REFERENCES projects (name) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_projects(self):
        """Load existing projects from configuration."""
        for project_name in self.config.list_projects():
            try:
                project_config = self.config.load_project_config(project_name)
                if project_config:
                    project = Project(project_config, self.config)
                    self._projects[project_name] = project
            except Exception as e:
                logger.error(f"Failed to load project {project_name}: {e}")
    
    def create_project(
        self,
        name: str,
        path: str,
        build_command: str,
        start_command: str,
        port: int = 3000,
        project_type: str = "nextjs"
    ) -> Project:
        """Create a new project."""
        if name in self._projects:
            raise ValueError(f"Project {name} already exists")
        
        # Validate project path
        project_path = Path(path).absolute()
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {path}")
        
        # Create configuration
        project_config = ProjectConfig(
            name=name,
            type=project_type,
            path=str(project_path),
            build=BuildConfig(command=build_command),
            start=StartConfig(command=start_command, port=port)
        )
        
        # Save configuration
        self.config.save_project_config(project_config)
        
        # Create project instance
        project = Project(project_config, self.config)
        self._projects[name] = project
        
        # Update database
        self._update_project_db(project)
        
        logger.info(f"Created project {name}")
        return project
    
    def get_project(self, name: str) -> Optional[Project]:
        """Get a project by name."""
        return self._projects.get(name)
    
    def list_projects(self) -> List[Project]:
        """List all projects."""
        return list(self._projects.values())
    
    def remove_project(self, name: str, cleanup_files: bool = False) -> bool:
        """Remove a project."""
        if name not in self._projects:
            logger.warning(f"Project {name} not found")
            return False
        
        project = self._projects[name]
        
        # Stop if running
        if project.is_running:
            asyncio.create_task(project.stop())
        
        # Remove from memory
        del self._projects[name]
        
        # Remove configuration
        self.config.delete_project_config(name)
        
        # Remove from database
        db_path = self.config.data_dir / "projects.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE name = ?", (name,))
        cursor.execute("DELETE FROM domains WHERE project_name = ?", (name,))
        conn.commit()
        conn.close()
        
        logger.info(f"Removed project {name}")
        return True
    
    def add_domain_to_project(self, project_name: str, domain: str, 
                             ssl: bool = True, is_primary: bool = False) -> bool:
        """Add a domain to a project."""
        project = self.get_project(project_name)
        if not project:
            logger.error(f"Project {project_name} not found")
            return False
        
        # Check if domain already exists
        for domain_config in project.config.domains:
            if domain_config.domain == domain:
                logger.warning(f"Domain {domain} already exists for project {project_name}")
                return False
        
        # Add domain configuration
        domain_config = DomainConfig(domain=domain, ssl=ssl)
        
        if is_primary or not project.config.domains:
            project.config.domains.insert(0, domain_config)
        else:
            project.config.domains.append(domain_config)
        
        # Save updated configuration
        self.config.save_project_config(project.config)
        
        # Update database
        db_path = self.config.data_dir / "projects.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO domains (project_name, domain, is_primary, ssl_enabled) VALUES (?, ?, ?, ?)",
            (project_name, domain, is_primary, ssl)
        )
        conn.commit()
        conn.close()
        
        logger.info(f"Added domain {domain} to project {project_name}")
        return True
    
    def get_project_by_domain(self, domain: str) -> Optional[Project]:
        """Get project associated with a domain."""
        for project in self._projects.values():
            if domain in project.get_all_domains():
                return project
        return None
    
    def _update_project_db(self, project: Project):
        """Update project information in database."""
        db_path = self.config.data_dir / "projects.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO projects (name, path, type, status, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            project.name,
            project.config.path,
            project.config.type,
            'running' if project.is_running else 'stopped',
            datetime.now().isoformat()
        ))
        
        # Update domains
        cursor.execute("DELETE FROM domains WHERE project_name = ?", (project.name,))
        for i, domain_config in enumerate(project.config.domains):
            cursor.execute('''
                INSERT INTO domains (project_name, domain, is_primary, ssl_enabled)
                VALUES (?, ?, ?, ?)
            ''', (
                project.name,
                domain_config.domain,
                i == 0,  # First domain is primary
                domain_config.ssl
            ))
        
        conn.commit()
        conn.close()
