"""
Setup script for LPES (Local Production Environment Simulator).
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text().strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="lpes",
    version="0.1.0",
    author="LPES Development Team",
    author_email="dev@lpes.local",
    description="Local Production Environment Simulator for NextJS and web applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dananjayahbi/Local-Production-Environment-Simulator--LPES-",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "lpes=lpes.cli.main:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "lpes": ["*.yaml", "*.json"],
    },
)
