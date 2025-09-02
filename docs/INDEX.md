# LPES Documentation Index

Welcome to the Local Production Environment Simulator (LPES) documentation.

## 📚 Documentation Structure

### 🚀 Getting Started
- **[README.md](README.md)** - Main documentation and quick start guide
- **[Installation Guide](#installation)** - Detailed installation instructions
- **[Project Setup](#project-setup)** - Setting up your first project

### 💻 User Guides
- **[Command Line Interface](COMMAND_EXAMPLES.md)** - CLI usage examples for all platforms
- **[GUI User Guide](GUI_README.md)** - Complete graphical interface documentation
- **[Project Management Guide](PROJECT_MANAGEMENT_GUIDE.md)** - Comprehensive project management
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions

### 🛠️ Development
- **[Project Summary](PROJECT_SUMMARY.md)** - Complete feature overview and architecture
- **[API Documentation](#api-docs)** - Module and class references
- **[Contributing Guide](#contributing)** - How to contribute to LPES

### 📋 Reference
- **[Configuration Reference](#config-ref)** - All configuration options
- **[CLI Command Reference](#cli-ref)** - Complete command documentation
- **[Examples and Templates](#examples)** - Sample projects and configurations

## 🏃‍♂️ Quick Start

### Installation
```bash
# Clone repository
git clone https://github.com/dananjayahbi/Local-Production-Environment-Simulator--LPES-.git
cd Local-Production-Environment-Simulator--LPES-

# Install dependencies
pip install -r requirements.txt

# Install LPES
pip install -e .
```

### Choose Your Interface

#### 🎨 GUI Interface (Recommended for Beginners)
```bash
# Launch modern GUI
python scripts/launch_gui.py

# Or use batch file (Windows)
scripts/launch_gui.bat
```

#### 💻 Command Line Interface
```bash
# From src directory
python src/main.py --help

# Create a project
python src/main.py init myapp --path "/path/to/project" --build "npm run build" --start "npm start" --port 3000
```

## 📖 Documentation Topics

### Installation

#### System Requirements
- **Python 3.9+**: Core runtime environment
- **Administrator Privileges**: For hosts file modification and port 443 binding
- **tkinter**: For GUI interface (usually included with Python)

#### Installation Methods

**Method 1: Development Installation**
```bash
pip install -e .
```

**Method 2: Direct Installation**
```bash
pip install -r requirements.txt
python setup.py install
```

**Method 3: Package Installation**
```bash
pip install lpes  # When published to PyPI
```

### Project Setup

#### Creating Your First Project

**GUI Method:**
1. Launch GUI: `python scripts/launch_gui.py`
2. Click "➕ New Project"
3. Fill in project details
4. Enable auto-domain and SSL options
5. Click "✅ Create Project"

**CLI Method:**
```bash
# PowerShell (Windows)
python src/main.py init myapp `
  --path "E:\path\to\project" `
  --build "npm run build" `
  --start "npm start" `
  --port 3000

# Bash (Linux/macOS)
python src/main.py init myapp \
  --path "/path/to/project" \
  --build "npm run build" \
  --start "npm start" \
  --port 3000
```

#### Adding Domains and SSL
```bash
# Add domain with SSL
python src/main.py domain add myapp myapp.local --ssl --hosts-file

# Build and start project
python src/main.py build myapp
python src/main.py start myapp

# Start proxy for HTTPS
python src/main.py proxy start
```

### API Documentation {#api-docs}

#### Core Modules

**lpes.core.config**
- `LPESConfig`: Main configuration class
- `ProjectConfig`: Project-specific configuration
- `DomainConfig`: Domain configuration with SSL

**lpes.core.project_manager**
- `ProjectManager`: Complete project lifecycle management
- `Project`: Individual project operations

**lpes.ssl.manager**
- `SSLManager`: SSL certificate generation and management
- Certificate Authority (CA) management

**lpes.proxy.server**
- `ProxyServer`: HTTPS reverse proxy with SSL termination
- WebSocket support and request forwarding

**lpes.dns.server**
- `DNSServerManager`: Local DNS server implementation
- `HostsFileManager`: Hosts file modification

**lpes.build.monitor**
- `BuildMonitor`: Build process management and monitoring
- Build caching and incremental builds

### Configuration Reference {#config-ref}

#### Global Configuration
```yaml
# ~/.lpes/config.yaml
ssl:
  ca_path: ~/.lpes/ssl/ca
  cert_path: ~/.lpes/ssl/certs
  
proxy:
  port: 443
  enable_websockets: true
  
dns:
  enabled: false
  port: 53
```

#### Project Configuration
```yaml
# ~/.lpes/projects/{project_name}.yaml
project:
  name: "myapp"
  path: "/path/to/project"
  type: "nextjs"
  
build:
  command: "npm run build"
  output_dir: "dist"
  
start:
  command: "npm start"
  port: 3000
  
domains:
  - name: "myapp.local"
    ssl: true
    hosts_file: true
```

### CLI Command Reference {#cli-ref}

#### Project Commands
```bash
# Project lifecycle
lpes init <name> --path <path> --build <cmd> --start <cmd> --port <port>
lpes list
lpes build <name>
lpes start <name>
lpes stop <name>
lpes restart <name>
lpes remove <name> [--cleanup]

# Domain management
lpes domain add <project> <domain> [--ssl] [--hosts-file]
lpes domain list <project>
lpes domain remove <project> <domain>

# SSL management
lpes ssl list
lpes ssl generate <domain>
lpes ssl trust-info

# Proxy management
lpes proxy start [--port <port>]
lpes proxy stop
lpes proxy status
```

### Examples and Templates {#examples}

#### NextJS Project
```bash
lpes init nextjs-app \
  --path "/path/to/nextjs" \
  --build "npm run build" \
  --start "npm start" \
  --port 3000
```

#### Vite Project
```bash
lpes init vite-app \
  --path "/path/to/vite" \
  --build "npm run build" \
  --start "npm run preview" \
  --port 4173
```

#### Custom Project
```bash
lpes init custom-app \
  --path "/path/to/custom" \
  --build "make build" \
  --start "./start.sh" \
  --port 8080
```

### Contributing {#contributing}

#### Development Setup
```bash
# Clone repository
git clone https://github.com/dananjayahbi/Local-Production-Environment-Simulator--LPES-.git
cd Local-Production-Environment-Simulator--LPES-

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Format code
black src/
flake8 src/
```

#### Project Structure
```
LPES/
├── src/                 # Source code
│   ├── lpes/           # Main package
│   └── main.py         # CLI entry point
├── gui/                 # GUI interfaces
├── scripts/             # Utility scripts
├── docs/               # Documentation
├── examples/           # Example projects
├── tests/              # Test suites
└── requirements.txt    # Dependencies
```

## 🔗 External Links

- **[GitHub Repository](https://github.com/dananjayahbi/Local-Production-Environment-Simulator--LPES-)**
- **[Issue Tracker](https://github.com/dananjayahbi/Local-Production-Environment-Simulator--LPES-/issues)**
- **[Releases](https://github.com/dananjayahbi/Local-Production-Environment-Simulator--LPES-/releases)**

## 📞 Support

- **Documentation**: Check this docs directory
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Email**: dev@lpes.local (if available)

---

**Happy local development with production-like features! 🚀**
