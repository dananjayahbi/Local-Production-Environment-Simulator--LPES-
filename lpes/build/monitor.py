"""
Build system for LPES projects.
Handles build execution, monitoring, and optimization.
"""

import asyncio
import logging
import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

from lpes.core.config import LPESConfig, ProjectConfig


logger = logging.getLogger(__name__)


class BuildCache:
    """Build cache for incremental builds."""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "build_cache.json"
        self._cache_data = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache data from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load build cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save cache data to disk."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self._cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save build cache: {e}")
    
    def get_file_hash(self, file_path: Path) -> str:
        """Get hash for a file."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def get_directory_hash(self, dir_path: Path, 
                          include_patterns: List[str] = None,
                          exclude_patterns: List[str] = None) -> str:
        """Get hash for a directory structure."""
        include_patterns = include_patterns or ["*"]
        exclude_patterns = exclude_patterns or [".git", "node_modules", ".next", "dist", "build"]
        
        hash_input = []
        
        for pattern in include_patterns:
            for file_path in dir_path.rglob(pattern):
                if file_path.is_file():
                    # Check if file should be excluded
                    relative_path = file_path.relative_to(dir_path)
                    should_exclude = any(
                        exclude_pattern in str(relative_path) 
                        for exclude_pattern in exclude_patterns
                    )
                    
                    if not should_exclude:
                        file_hash = self.get_file_hash(file_path)
                        hash_input.append(f"{relative_path}:{file_hash}")
        
        combined = "|".join(sorted(hash_input))
        return hashlib.md5(combined.encode()).hexdigest()
    
    def is_cache_valid(self, project_name: str, source_hash: str) -> bool:
        """Check if cache is valid for a project."""
        if project_name not in self._cache_data:
            return False
        
        cache_entry = self._cache_data[project_name]
        return cache_entry.get("source_hash") == source_hash
    
    def update_cache(self, project_name: str, source_hash: str, 
                    build_artifacts: List[str] = None):
        """Update cache entry for a project."""
        self._cache_data[project_name] = {
            "source_hash": source_hash,
            "last_build": datetime.now().isoformat(),
            "build_artifacts": build_artifacts or []
        }
        self._save_cache()
    
    def get_cache_info(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get cache information for a project."""
        return self._cache_data.get(project_name)
    
    def clear_cache(self, project_name: str = None):
        """Clear cache for a project or all projects."""
        if project_name:
            self._cache_data.pop(project_name, None)
        else:
            self._cache_data.clear()
        self._save_cache()


class BuildSession:
    """Represents a single build session."""
    
    def __init__(self, project_config: ProjectConfig, build_cache: BuildCache):
        self.project_config = project_config
        self.build_cache = build_cache
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.success = False
        self.error_message: Optional[str] = None
        self.output_lines: List[str] = []
        self.process: Optional[asyncio.subprocess.Process] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get build duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    async def execute(self, 
                     on_output: Optional[Callable[[str], None]] = None,
                     on_error: Optional[Callable[[str], None]] = None,
                     force_rebuild: bool = False) -> bool:
        """Execute the build process."""
        self.start_time = datetime.now()
        logger.info(f"Starting build for {self.project_config.name}")
        
        try:
            # Check if incremental build is possible
            if not force_rebuild:
                project_path = Path(self.project_config.path)
                source_hash = self.build_cache.get_directory_hash(
                    project_path,
                    include_patterns=["*.js", "*.ts", "*.jsx", "*.tsx", "*.json", "*.md"],
                    exclude_patterns=[".git", "node_modules", ".next", "dist", "build"]
                )
                
                if self.build_cache.is_cache_valid(self.project_config.name, source_hash):
                    logger.info(f"Build cache valid for {self.project_config.name}, skipping build")
                    self.success = True
                    self.end_time = datetime.now()
                    return True
            
            # Run pre-build commands
            for cmd in self.project_config.build.pre_build:
                success = await self._run_command(cmd, on_output, on_error, timeout=60)
                if not success:
                    self.error_message = f"Pre-build command failed: {cmd}"
                    return False
            
            # Run main build command
            success = await self._run_command(
                self.project_config.build.command,
                on_output, 
                on_error,
                env=self.project_config.build.env,
                timeout=self.project_config.build.timeout
            )
            
            if not success:
                self.error_message = "Build command failed"
                return False
            
            # Run post-build commands
            for cmd in self.project_config.build.post_build:
                success = await self._run_command(cmd, on_output, on_error, timeout=60)
                if not success:
                    logger.warning(f"Post-build command failed: {cmd}")
                    # Don't fail the build for post-build command failures
            
            # Update cache
            if not force_rebuild:
                self.build_cache.update_cache(
                    self.project_config.name,
                    source_hash,
                    self._detect_build_artifacts()
                )
            
            self.success = True
            logger.info(f"Build completed successfully for {self.project_config.name}")
            return True
            
        except Exception as e:
            self.error_message = str(e)
            logger.error(f"Build failed for {self.project_config.name}: {e}")
            return False
        
        finally:
            self.end_time = datetime.now()
    
    async def _run_command(self, 
                          command: str,
                          on_output: Optional[Callable[[str], None]] = None,
                          on_error: Optional[Callable[[str], None]] = None,
                          env: Optional[Dict[str, str]] = None,
                          timeout: int = 300) -> bool:
        """Run a build command."""
        try:
            # Prepare environment
            cmd_env = os.environ.copy()
            if env:
                cmd_env.update(env)
            
            logger.debug(f"Running command: {command}")
            
            # Start process
            self.process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_config.path,
                env=cmd_env
            )
            
            # Monitor output
            if on_output or on_error:
                stdout_task = asyncio.create_task(
                    self._stream_output(self.process.stdout, on_output, "stdout")
                )
                stderr_task = asyncio.create_task(
                    self._stream_output(self.process.stderr, on_error, "stderr")
                )
            
            # Wait for completion with timeout
            try:
                await asyncio.wait_for(self.process.wait(), timeout=timeout)
                
                if on_output or on_error:
                    await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
                
                return self.process.returncode == 0
                
            except asyncio.TimeoutError:
                logger.error(f"Command timeout after {timeout}s: {command}")
                self.process.kill()
                await self.process.wait()
                return False
                
        except Exception as e:
            logger.error(f"Failed to run command '{command}': {e}")
            return False
    
    async def _stream_output(self, 
                           stream: asyncio.StreamReader,
                           callback: Optional[Callable[[str], None]],
                           stream_type: str):
        """Stream process output to callback."""
        try:
            while True:
                line = await stream.readline()
                if not line:
                    break
                
                line_str = line.decode().rstrip()
                self.output_lines.append(f"[{stream_type}] {line_str}")
                
                if callback:
                    callback(line_str)
                    
        except Exception as e:
            logger.warning(f"Error streaming {stream_type}: {e}")
    
    def _detect_build_artifacts(self) -> List[str]:
        """Detect build artifacts that were created."""
        artifacts = []
        project_path = Path(self.project_config.path)
        
        # Common build output directories
        artifact_dirs = [".next", "dist", "build", "out"]
        
        for dir_name in artifact_dirs:
            artifact_dir = project_path / dir_name
            if artifact_dir.exists() and artifact_dir.is_dir():
                artifacts.append(str(artifact_dir.relative_to(project_path)))
        
        return artifacts
    
    def get_summary(self) -> Dict[str, Any]:
        """Get build session summary."""
        return {
            "project": self.project_config.name,
            "success": self.success,
            "duration": self.duration,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error_message": self.error_message,
            "output_lines": len(self.output_lines)
        }


class BuildMonitor:
    """Monitors and manages build processes."""
    
    def __init__(self, config: Optional[LPESConfig] = None):
        self.config = config or LPESConfig()
        self.build_cache = BuildCache(self.config.data_dir / "build_cache")
        self.active_builds: Dict[str, BuildSession] = {}
        self.build_history: List[BuildSession] = []
        self.max_history = 50
    
    async def execute_build(self, 
                           project_config: ProjectConfig,
                           on_output: Optional[Callable[[str], None]] = None,
                           on_error: Optional[Callable[[str], None]] = None,
                           force_rebuild: bool = False) -> BuildSession:
        """Execute a build for a project."""
        project_name = project_config.name
        
        if project_name in self.active_builds:
            logger.warning(f"Build already in progress for {project_name}")
            return self.active_builds[project_name]
        
        # Create build session
        session = BuildSession(project_config, self.build_cache)
        self.active_builds[project_name] = session
        
        try:
            # Execute build
            await session.execute(on_output, on_error, force_rebuild)
            
            # Add to history
            self.build_history.append(session)
            if len(self.build_history) > self.max_history:
                self.build_history.pop(0)
            
            return session
            
        finally:
            # Remove from active builds
            self.active_builds.pop(project_name, None)
    
    def is_building(self, project_name: str) -> bool:
        """Check if a project is currently building."""
        return project_name in self.active_builds
    
    def get_active_builds(self) -> List[str]:
        """Get list of projects currently building."""
        return list(self.active_builds.keys())
    
    def get_build_history(self, project_name: str = None) -> List[BuildSession]:
        """Get build history for a project or all projects."""
        if project_name:
            return [s for s in self.build_history if s.project_config.name == project_name]
        return self.build_history.copy()
    
    def get_build_stats(self, project_name: str = None) -> Dict[str, Any]:
        """Get build statistics."""
        sessions = self.get_build_history(project_name)
        
        if not sessions:
            return {
                "total_builds": 0,
                "successful_builds": 0,
                "failed_builds": 0,
                "success_rate": 0.0,
                "average_duration": 0.0
            }
        
        successful = [s for s in sessions if s.success]
        failed = [s for s in sessions if not s.success]
        durations = [s.duration for s in sessions if s.duration is not None]
        
        return {
            "total_builds": len(sessions),
            "successful_builds": len(successful),
            "failed_builds": len(failed),
            "success_rate": len(successful) / len(sessions) * 100,
            "average_duration": sum(durations) / len(durations) if durations else 0.0,
            "last_build": sessions[-1].get_summary() if sessions else None
        }
    
    def clear_cache(self, project_name: str = None):
        """Clear build cache."""
        self.build_cache.clear_cache(project_name)
        logger.info(f"Cleared build cache for {project_name if project_name else 'all projects'}")
    
    def cancel_build(self, project_name: str) -> bool:
        """Cancel an active build."""
        if project_name not in self.active_builds:
            return False
        
        session = self.active_builds[project_name]
        if session.process:
            try:
                session.process.terminate()
                logger.info(f"Cancelled build for {project_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to cancel build for {project_name}: {e}")
        
        return False
