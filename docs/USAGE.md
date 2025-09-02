# LPES Usage Guide

## Complete Setup and Usage Example

This guide demonstrates how to set up and use LPES (Local Production Environment Simulator) with a real NextJS project.

## Prerequisites

1. **Python 3.9+** installed
2. **Node.js and npm** for NextJS projects
3. **Administrator/sudo privileges** (for hosts file modification or port 443)

## Installation

```bash
# Clone the repository
git clone https://github.com/dananjayahbi/Local-Production-Environment-Simulator--LPES-.git
cd Local-Production-Environment-Simulator--LPES-

# Install dependencies
pip install -r requirements.txt

# Test installation
python main.py --help
```

## Quick Start with NextJS

### 1. Create a NextJS Project (if you don't have one)

```bash
# Create a new NextJS project
npx create-next-app@latest my-nextjs-app
cd my-nextjs-app

# Test that it works
npm run build
npm run dev
# Visit http://localhost:3000 to verify it works
# Press Ctrl+C to stop
```

### 2. Initialize LPES

```bash
# Navigate to LPES directory
cd path/to/Local-Production-Environment-Simulator--LPES-

# Initialize your NextJS project with LPES
python main.py init my-app \
  --path /path/to/my-nextjs-app \
  --build "npm run build" \
  --start "npm start" \
  --port 3000
```

### 3. Add Custom Domain

```bash
# Add a custom domain with SSL
python main.py domain add my-app myapp.local --ssl --hosts-file

# This will:
# - Generate an SSL certificate for myapp.local
# - Add myapp.local to your system's hosts file (requires admin privileges)
```

### 4. Build and Start Project

```bash
# Build the project
python main.py build my-app

# Start the project
python main.py start my-app

# Your NextJS app is now running on http://localhost:3000
```

### 5. Start HTTPS Proxy

```bash
# Start the HTTPS proxy server
python main.py proxy start

# If port 443 requires admin privileges, it will fall back to 8443
# Your app is now available at:
# - http://localhost:3000 (direct)
# - https://myapp.local (via HTTPS proxy)
```

### 6. Trust SSL Certificate (One-time setup)

```bash
# Get instructions for trusting the CA certificate
python main.py ssl trust-info

# Follow the platform-specific instructions to avoid browser warnings
```

## Advanced Usage

### Multiple Projects

```bash
# Initialize multiple projects
python main.py init frontend --path /path/to/frontend --build "npm run build" --start "npm start" --port 3000
python main.py init admin --path /path/to/admin --build "npm run build" --start "npm start" --port 3001
python main.py init api --path /path/to/api --build "npm run build" --start "npm start" --port 4000

# Add domains
python main.py domain add frontend app.local --ssl
python main.py domain add admin admin.app.local --ssl
python main.py domain add api api.app.local --ssl

# Start all projects
python main.py start frontend
python main.py start admin
python main.py start api

# Start proxy (serves all domains)
python main.py proxy start
```

### Project Management

```bash
# List all projects
python main.py list

# Check project status
python main.py list

# Stop a project
python main.py stop my-app

# Restart a project
python main.py restart my-app

# Remove a project (with cleanup)
python main.py remove my-app --cleanup
```

### Domain Management

```bash
# List all domains
python main.py domain list

# List domains for a specific project
python main.py domain list my-app

# Add additional domains to a project
python main.py domain add my-app www.myapp.local --ssl
python main.py domain add my-app api.myapp.local --ssl
```

### SSL Certificate Management

```bash
# List all SSL certificates
python main.py ssl list

# Generate certificate for a specific domain
python main.py ssl generate example.local

# Get CA trust instructions
python main.py ssl trust-info
```

### Build Management

```bash
# Build with cache
python main.py build my-app

# Force rebuild (skip cache)
python main.py build my-app --force

# Build before starting
python main.py start my-app --build-first
```

## Configuration Examples

### NextJS with Environment Variables

```bash
# Initialize with production environment
python main.py init prod-app \
  --path /path/to/nextjs-app \
  --build "NODE_ENV=production npm run build" \
  --start "NODE_ENV=production npm start" \
  --port 3000
```

### NextJS with Custom Build Script

```bash
# For projects with custom build processes
python main.py init complex-app \
  --path /path/to/app \
  --build "npm install && npm run lint && npm run build" \
  --start "npm start" \
  --port 3000
```

## Troubleshooting

### Permission Issues

```bash
# If port 443 requires admin privileges
python main.py proxy start --fallback-port 8443

# If hosts file modification fails
# Manually add to hosts file:
# echo "127.0.0.1 myapp.local" >> /etc/hosts  # Linux/macOS
# or edit C:\Windows\System32\drivers\etc\hosts on Windows
```

### Certificate Trust Issues

```bash
# Get detailed trust instructions
python main.py ssl trust-info

# For development, you can ignore browser warnings
# or use browser flags: --ignore-certificate-errors-spki-list --ignore-ssl-errors
```

### Build Issues

```bash
# Check if build command works independently
cd /path/to/your/project
npm run build  # Test build command

# Force rebuild to skip cache
python main.py build my-app --force

# Check build logs
python main.py --verbose build my-app
```

### Port Conflicts

```bash
# If port 3000 is in use, specify different port
python main.py init my-app \
  --path /path/to/app \
  --build "npm run build" \
  --start "npm start" \
  --port 3001
```

## Real-World Example: E-commerce Site

```bash
# 1. Initialize the project
python main.py init ecommerce \
  --path /path/to/ecommerce-nextjs \
  --build "npm run build" \
  --start "npm start" \
  --port 3000

# 2. Add domains for different environments
python main.py domain add ecommerce shop.local --ssl --primary
python main.py domain add ecommerce admin.shop.local --ssl
python main.py domain add ecommerce api.shop.local --ssl

# 3. Build and start
python main.py build ecommerce
python main.py start ecommerce

# 4. Start proxy
python main.py proxy start

# 5. Access your e-commerce site
# - Main site: https://shop.local
# - Admin panel: https://admin.shop.local
# - API: https://api.shop.local
```

## Integration with Development Workflow

### VS Code Integration

Add to your VS Code tasks.json:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "LPES: Start Project",
      "type": "shell",
      "command": "python",
      "args": ["path/to/lpes/main.py", "start", "my-app"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "new"
      }
    },
    {
      "label": "LPES: Start Proxy",
      "type": "shell",
      "command": "python",
      "args": ["path/to/lpes/main.py", "proxy", "start"],
      "group": "build"
    }
  ]
}
```

### Package.json Scripts

Add to your NextJS project's package.json:

```json
{
  "scripts": {
    "lpes:init": "python path/to/lpes/main.py init my-app --path . --build 'npm run build' --start 'npm start'",
    "lpes:start": "python path/to/lpes/main.py start my-app",
    "lpes:proxy": "python path/to/lpes/main.py proxy start",
    "lpes:build": "python path/to/lpes/main.py build my-app"
  }
}
```

## Performance Tips

1. **Use Build Cache**: Don't use `--force` unless necessary
2. **Minimize Domains**: Only add domains you actually need
3. **Use Alternative Ports**: If 443 requires admin privileges, use 8443
4. **Monitor Resources**: Use `python main.py list` to check project status

## Security Notes

1. **Only for Development**: LPES is designed for local development only
2. **Trust CA Certificate**: Add the LPES CA to your browser's trust store
3. **Firewall**: LPES only binds to localhost (127.0.0.1)
4. **Cleanup**: Remove projects when done to clean up certificates and hosts entries

## Getting Help

```bash
# General help
python main.py --help

# Command-specific help
python main.py init --help
python main.py domain add --help
python main.py proxy start --help

# Verbose output for debugging
python main.py --verbose list
python main.py --verbose build my-app
```
