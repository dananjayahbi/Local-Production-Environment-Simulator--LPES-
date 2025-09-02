# LPES - Local Production Environment Simulator

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

LPES (Local Production Environment Simulator) is a Python-based development tool designed to replicate production server environments on local machines. It enables developers to test web applications, particularly NextJS applications, with production-like configurations including HTTPS, custom domain names, and SSL certificates.

## 🚀 Features

- **HTTPS Support**: Automatic SSL certificate generation and management
- **Custom Domains**: Use production-like domain names locally (e.g., `myapp.local`)
- **Reverse Proxy**: HTTPS termination and request forwarding to local development servers
- **Build System Integration**: Automated build and deployment processes
- **Process Management**: Monitor and manage application lifecycle
- **DNS Resolution**: Local DNS server or hosts file management
- **Rich CLI Interface**: Comprehensive command-line interface with real-time feedback
- **🎨 Modern GUI**: Graphical interface for visual project management (NEW!)

## 📋 Requirements

- Python 3.9 or higher
- Administrator/sudo privileges (for hosts file modification or port 443 binding)
- NextJS or other web application project
- tkinter (for GUI interface - usually included with Python)

## 🛠️ Installation

### Option 1: Install from Source

```bash
# Clone the repository
git clone https://github.com/dananjayahbi/Local-Production-Environment-Simulator--LPES-.git
cd Local-Production-Environment-Simulator--LPES-

# Install dependencies
pip install -r requirements.txt

# Install LPES
pip install -e .
```

### Option 2: Direct Installation

```bash
pip install -r requirements.txt
python setup.py install
```

## 🚀 Quick Start

### Choose Your Interface

#### 🎨 Option A: Modern GUI Interface (Recommended)
```bash
# Launch the modern graphical interface - no more command typing!
python lpes_gui_enhanced.py
```

**✨ GUI Features:**
- 📋 **Visual Project Management**: Create, view, and delete projects with forms
- 🎮 **One-Click Actions**: Build, start, stop projects with buttons
- 📟 **Integrated Console**: Real-time logs with color coding
- 🔄 **Proxy Controls**: Start/stop proxy server visually
- 🔒 **SSL Management**: Certificate generation and CA trust info
- 🌐 **Domain Setup**: Auto-create domains with SSL during project creation

#### 💻 Option B: Command Line Interface

### 1. Initialize a Project

```bash
# Navigate to your NextJS project directory
cd /path/to/your/nextjs-project

# Initialize LPES for your project
# PowerShell (Windows) - use backticks for line continuation:
python main.py init myapp `
  --path . `
  --build "npm run build" `
  --start "npm run start" `
  --port 3000

# Bash/Linux/macOS - use backslashes for line continuation:
python main.py init myapp \
  --path . \
  --build "npm run build" \
  --start "npm run start" \
  --port 3000

# Single line (works in all shells):
python main.py init myapp --path . --build "npm run build" --start "npm run start" --port 3000
```

### 2. Add a Domain

```bash
# Add a custom domain
python main.py domain add myapp myapp.local --ssl --hosts-file

# This will:
# - Add the domain to your project
# - Generate an SSL certificate
# - Add the domain to your hosts file
```

### 3. Build and Start

```bash
# Build your project
python main.py build myapp

# Start your project
python main.py start myapp

# Start the HTTPS proxy server
python main.py proxy start
```

### 4. Access Your Application

Open your browser and navigate to:
- **HTTPS**: `https://myapp.local`
- **HTTP**: `http://localhost:3000`

## 📖 Usage Examples

### Managing Projects

```bash
# List all projects
python main.py list

# Remove a project
python main.py remove myapp --cleanup

# Restart a project
python main.py restart myapp
```

### Domain Management

```bash
# List domains
python main.py domain list

# Add additional domains
python main.py domain add myapp api.myapp.local --ssl
python main.py domain add myapp admin.myapp.local --ssl
```

### SSL Certificate Management

```bash
# List certificates
python main.py ssl list

# Generate certificate for a domain
python main.py ssl generate example.local

# Get trust instructions
python main.py ssl trust-info
```

### Proxy Server

```bash
# Start proxy on default port (443)
python main.py proxy start

# Start on alternative port
python main.py proxy start --port 8443

# Stop proxy
python main.py proxy stop
```

## 🔧 Configuration

LPES uses YAML configuration files stored in `~/.lpes/`. Each project has its own configuration file.

### Example Project Configuration

```yaml
project:
  name: "my-nextjs-app"
  type: "nextjs"
  path: "/path/to/project"
  
  build:
    command: "npm run build"
    env:
      NODE_ENV: "production"
      NEXT_PUBLIC_API_URL: "https://api.myapp.local"
    pre_build:
      - "npm install"
    timeout: 300
  
  start:
    command: "npm run start"
    port: 3000
    env:
      NODE_ENV: "production"
  
  domains:
    - domain: "myapp.local"
      ssl: true
      subdomains: ["www", "api"]
  
  ssl:
    auto_generate: true
```

## 🛡️ SSL Certificate Trust

To avoid browser security warnings, you need to trust the LPES Certificate Authority:

```bash
# Get trust instructions
python main.py ssl trust-info
```

Follow the platform-specific instructions to add the CA certificate to your system's trust store.

## 🏗️ Architecture

LPES consists of several core components:

- **Project Manager**: Handles project lifecycle and configuration
- **SSL Manager**: Generates and manages SSL certificates
- **Proxy Server**: HTTPS reverse proxy with SSL termination
- **DNS Server**: Local DNS resolution for custom domains
- **Build Monitor**: Manages build processes and caching
- **CLI Interface**: Rich command-line interface

## 🐛 Troubleshooting

### Common Issues

1. **Permission Denied on Port 443**
   ```bash
   # Use fallback port
   python main.py proxy start --port 8443
   ```

2. **Certificate Not Trusted**
   ```bash
   # Follow trust instructions
   lpes ssl trust-info
   ```

3. **Domain Not Resolving**
   ```bash
   # Add domain to hosts file
   lpes domain add myapp myapp.local --hosts-file
   ```

4. **Build Failures**
   ```bash
   # Force rebuild (skip cache)
   lpes build myapp --force
   ```

### Logs and Debugging

```bash
# Enable verbose output
lpes --verbose list

# Check proxy health
curl -k https://localhost:8443/_lpes/health
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/dananjayahbi/Local-Production-Environment-Simulator--LPES-.git
cd Local-Production-Environment-Simulator--LPES-

# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
python -m pytest tests/

# Run linting
flake8 lpes/
black lpes/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [aiohttp](https://docs.aiohttp.org/) for the async HTTP server
- [cryptography](https://cryptography.io/) for SSL certificate management
- [click](https://click.palletsprojects.com/) for the CLI framework
- [rich](https://rich.readthedocs.io/) for beautiful terminal output

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/dananjayahbi/Local-Production-Environment-Simulator--LPES-/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dananjayahbi/Local-Production-Environment-Simulator--LPES-/discussions)

---

Made with ❤️ by the LPES Development Team
