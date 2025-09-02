"""
LPES Setup Script
Production-grade installation script for Local Production Environment Simulator.
"""

from setuptools import setup, find_packages
from pathlib import Path
import sys

# Ensure Python 3.9+
if sys.version_info < (3, 9):
    print("❌ LPES requires Python 3.9 or higher")
    print(f"Current version: {sys.version}")
    sys.exit(1)

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = ""
try:
    long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
except Exception:
    print("⚠️  Could not read README.md")

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    try:
        requirements = requirements_path.read_text().strip().split('\n')
        requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]
    except Exception:
        print("⚠️  Could not read requirements.txt, using defaults")

# Fallback requirements if file not found
if not requirements:
    requirements = [
        "aiohttp>=3.9.0",
        "cryptography>=41.0.0", 
        "click>=8.1.0",
        "rich>=13.0.0",
        "pydantic>=2.0.0",
        "dnslib>=0.9.0",
        "pyyaml>=6.0.0"
    ]

setup(
    name="lpes",
    version="1.0.0",
    author="LPES Development Team",
    author_email="dev@lpes.local",
    description="Local Production Environment Simulator for NextJS and web applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dananjayahbi/Local-Production-Environment-Simulator--LPES-",
    project_urls={
        "Bug Reports": "https://github.com/dananjayahbi/Local-Production-Environment-Simulator--LPES-/issues",
        "Source": "https://github.com/dananjayahbi/Local-Production-Environment-Simulator--LPES-",
        "Documentation": "https://github.com/dananjayahbi/Local-Production-Environment-Simulator--LPES-/blob/main/docs/",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: Web Environment", 
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="development, local, production, simulator, nextjs, ssl, proxy, dns, web, https",
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "gui": [],  # tkinter is usually included with Python
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "lpes=lpes.cli.main:cli",
            "lpes-gui=lpes.gui_launcher:main",
        ],
    },
    include_package_data=True,
    package_data={
        "lpes": ["*.yaml", "*.json", "*.md"],
    },
    zip_safe=False,
)
