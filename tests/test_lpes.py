"""
Basic tests for LPES components.
"""

import pytest
import tempfile
import asyncio
from pathlib import Path

from lpes.core.config import LPESConfig, ProjectConfig, BuildConfig, StartConfig, DomainConfig
from lpes.core.project_manager import ProjectManager
from lpes.ssl.manager import SSLManager
from lpes.build.monitor import BuildMonitor


class TestConfig:
    """Test configuration management."""
    
    def test_global_config_creation(self):
        """Test global configuration creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LPESConfig(tmpdir)
            assert config.data_dir.exists()
            assert config.config_file.exists()
    
    def test_project_config_validation(self):
        """Test project configuration validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_project_dir = Path(tmpdir) / "test_project"
            test_project_dir.mkdir()
            
            project_config = ProjectConfig(
                name="test",
                path=str(test_project_dir),
                build=BuildConfig(command="echo 'build'"),
                start=StartConfig(command="echo 'start'"),
                domains=[DomainConfig(domain="test.local")]
            )
            
            assert project_config.name == "test"
            assert project_config.domains[0].domain == "test.local"


class TestProjectManager:
    """Test project management."""
    
    def test_project_creation(self):
        """Test creating a new project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LPESConfig(tmpdir)
            manager = ProjectManager(config)
            
            test_project_dir = Path(tmpdir) / "test_project"
            test_project_dir.mkdir()
            
            project = manager.create_project(
                name="test",
                path=str(test_project_dir),
                build_command="echo 'build'",
                start_command="echo 'start'"
            )
            
            assert project.name == "test"
            assert project.config.path == str(test_project_dir)
    
    def test_domain_addition(self):
        """Test adding domains to projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LPESConfig(tmpdir)
            manager = ProjectManager(config)
            
            test_project_dir = Path(tmpdir) / "test_project"
            test_project_dir.mkdir()
            
            project = manager.create_project(
                name="test",
                path=str(test_project_dir),
                build_command="echo 'build'",
                start_command="echo 'start'"
            )
            
            success = manager.add_domain_to_project("test", "test.local")
            assert success
            
            updated_project = manager.get_project("test")
            assert len(updated_project.config.domains) == 1
            assert updated_project.config.domains[0].domain == "test.local"


class TestSSLManager:
    """Test SSL certificate management."""
    
    def test_ca_creation(self):
        """Test Certificate Authority creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LPESConfig(tmpdir)
            ssl_manager = SSLManager(config)
            
            # CA should be created automatically
            assert config.get_ca_cert_path().exists()
            assert config.get_ca_key_path().exists()
    
    def test_certificate_generation(self):
        """Test SSL certificate generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LPESConfig(tmpdir)
            ssl_manager = SSLManager(config)
            
            cert_path, key_path = ssl_manager.generate_certificate("test.local")
            
            assert Path(cert_path).exists()
            assert Path(key_path).exists()
            
            # Test certificate listing
            certificates = ssl_manager.list_certificates()
            assert len(certificates) == 1
            assert certificates[0][0] == "test.local"


class TestBuildMonitor:
    """Test build monitoring."""
    
    @pytest.mark.asyncio
    async def test_build_execution(self):
        """Test build execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LPESConfig(tmpdir)
            monitor = BuildMonitor(config)
            
            test_project_dir = Path(tmpdir) / "test_project"
            test_project_dir.mkdir()
            
            project_config = ProjectConfig(
                name="test",
                path=str(test_project_dir),
                build=BuildConfig(command="echo 'test build'"),
                start=StartConfig(command="echo 'test start'"),
                domains=[]
            )
            
            session = await monitor.execute_build(project_config)
            
            assert session.success
            assert session.duration is not None
            assert session.duration > 0


def run_tests():
    """Run all tests."""
    import subprocess
    import sys
    
    # Install pytest if not available
    try:
        import pytest
    except ImportError:
        print("Installing pytest...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"])
        import pytest
    
    # Run tests
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()
