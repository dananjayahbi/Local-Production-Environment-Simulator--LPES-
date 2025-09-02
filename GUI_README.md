# LPES GUI Manager

A modern graphical user interface for the Local Production Environment Simulator (LPES) that eliminates the need to execute command-line commands manually.

## 🎯 Features

### 📋 Project Management
- **Create Projects**: Visual project creation with form validation
- **List Projects**: View all projects in a modern table format
- **Delete Projects**: Safe project deletion with confirmation
- **Auto-Domain Setup**: Automatically create domains during project creation

### 🎮 Project Controls
- **Build Projects**: One-click project building
- **Start/Stop Projects**: Easy project lifecycle management
- **Domain Management**: Add custom domains with SSL
- **SSL Management**: Certificate generation and management

### 🔄 Proxy Server
- **Start/Stop Proxy**: Control the HTTPS proxy server
- **Status Indicators**: Visual proxy status monitoring
- **Port Configuration**: Custom proxy port settings

### 📟 Integrated Console
- **Real-time Logs**: See all LPES command output in real-time
- **Color-coded Logs**: Different colors for different log levels
- **Save Logs**: Export console output to files
- **Log Level Control**: Filter logs by severity

### 🔒 SSL Certificate Management
- **CA Trust Instructions**: Get certificate authority trust info
- **Certificate Listing**: View all generated certificates
- **Auto-SSL**: Automatic SSL certificate generation

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- LPES system installed and configured
- tkinter (usually included with Python)

### Launch Options

#### Option 1: Python Script
```bash
cd "E:\My_GitHub_Repos\Local-Production-Environment-Simulator--LPES-"
python lpes_gui_enhanced.py
```

#### Option 2: Batch File (Windows)
```bash
# Double-click or run:
launch_gui.bat
```

#### Option 3: Launcher Script
```bash
python launch_gui.py
```

## 📖 User Guide

### Creating a New Project

1. **Click "➕ New" button** in the Projects panel
2. **Fill in the form**:
   - **Project Name**: Unique identifier (e.g., "my-nextjs-app")
   - **Project Path**: Path to your project folder
   - **Build Command**: Command to build your project (e.g., "npm run build")
   - **Start Command**: Command to start your project (e.g., "npm start")
   - **Port**: Port number your project runs on (e.g., 3000)
3. **Configure Options**:
   - ✅ Auto-create domain: Creates `{name}.local` domain automatically
   - ✅ Generate SSL certificate: Creates SSL cert for HTTPS access
4. **Click "✅ Create Project"**

### Managing Existing Projects

#### Project Actions
- **🔨 Build**: Build the selected project
- **▶️ Start**: Start the selected project
- **⏹️ Stop**: Stop the selected project
- **🌐 Domain**: Add additional domains to the project
- **🔒 SSL**: Manage SSL certificates
- **📁 Open**: Open project folder in file explorer

#### Proxy Management
- **▶️ Start Proxy**: Start the HTTPS proxy server (required for SSL access)
- **⏹️ Stop Proxy**: Stop the proxy server
- **Status Indicator**: Shows proxy status in header

### Console and Logging

The integrated console shows:
- **Real-time Command Output**: All LPES command results
- **Color-coded Messages**: 
  - 🔵 Blue: Info messages
  - 🟢 Green: Success messages
  - 🟡 Yellow: Warning messages
  - 🔴 Red: Error messages
- **Timestamps**: All messages include precise timestamps
- **Auto-scroll**: Console automatically scrolls to latest messages

#### Console Controls
- **🧹 Clear**: Clear console output
- **💾 Save**: Save console log to file
- **Log Level**: Filter messages by severity (DEBUG, INFO, WARNING, ERROR)

## 🎨 Interface Overview

### Main Layout
```
┌─────────────────────────────────────────────────────────────┐
│ 🚀 LPES Manager Pro                    🔴 Proxy: Offline   │
├─────────────────┬───────────────────────────────────────────┤
│ 📋 Projects     │ 📟 Console                               │
│                 │                                           │
│ ┌─────────────┐ │ [09:15:23] INFO: LPES Manager started    │
│ │Name │Domain │ │ [09:15:24] INFO: Loading projects...     │
│ │app  │app... │ │ [09:15:25] SUCCESS: Found 2 projects     │
│ └─────────────┘ │                                           │
│                 │                                           │
│ 🎮 Quick Actions│ 🔄 Proxy    🔒 SSL                       │
│ [🔨][▶️][⏹️]   │                                           │
│ [🌐][🔒][📁]   │                                           │
└─────────────────┴───────────────────────────────────────────┤
│ Ready                           LPES Path: E:\LPES\...      │
└─────────────────────────────────────────────────────────────┘
```

### Projects Panel
- **Toolbar**: New, Refresh, Delete buttons
- **Projects Table**: Shows name, domain, status, port, type
- **Quick Actions**: Build, Start, Stop, Domain, SSL, Open buttons
- **Selection**: Click row to select project for actions

### Control Panel (Tabbed)
- **📟 Console Tab**: Real-time logging and output
- **🔄 Proxy Tab**: Proxy server controls
- **🔒 SSL Tab**: SSL certificate management

## 🛠️ Advanced Features

### Custom Project Types
The GUI supports various project types:
- **NextJS**: Modern React framework
- **Vite**: Fast build tool for modern web apps
- **Custom**: Any project with build/start commands

### Domain Configuration
- **Primary Domain**: Main domain for the project
- **Additional Domains**: Add multiple domains to one project
- **SSL Auto-Generation**: Automatic certificate creation
- **Hosts File Management**: Automatic hosts file updates

### Build System
- **Incremental Builds**: Only rebuild when files change
- **Build Caching**: Faster subsequent builds
- **Build Monitoring**: Real-time build progress
- **Error Handling**: Clear error messages for build failures

## 🔧 Configuration

### LPES Path
The GUI automatically detects the LPES installation directory. You can change it in:
- **Settings Tab** → LPES Directory → Browse

### Log Levels
Control console verbosity:
- **DEBUG**: All messages including debug info
- **INFO**: General information (default)
- **WARNING**: Important warnings only
- **ERROR**: Error messages only

## 🚨 Troubleshooting

### Common Issues

#### "Permission denied: Cannot modify hosts file"
**Solution**: Run the GUI as Administrator
1. Right-click PowerShell or Command Prompt
2. Select "Run as Administrator"
3. Launch the GUI from the admin terminal

#### "Project not found" errors
**Solution**: 
1. Click "🔄 Refresh" to reload projects
2. Check if project exists in LPES directory
3. Verify project was created successfully

#### Proxy server won't start
**Solution**:
1. Check if port 443 is available
2. Run as Administrator for port 443 access
3. Try alternative port in proxy settings

#### GUI won't start
**Solution**:
1. Ensure Python 3.9+ is installed
2. Check if tkinter is available: `python -c "import tkinter"`
3. Verify LPES is in the current directory

### Getting Help

#### Console Logs
All operations are logged to the integrated console with detailed error messages.

#### Command Verification
The GUI shows the exact LPES commands being executed, so you can run them manually if needed.

#### Log Export
Save console logs to file for detailed troubleshooting.

## 🎯 Tips and Best Practices

### Project Organization
- Use descriptive project names
- Group related projects with consistent naming
- Keep project paths organized

### SSL Certificates
- Always generate SSL certificates for local HTTPS
- Trust the CA certificate in your browser for security warnings
- Use `.local` domains for local development

### Performance
- Stop unused projects to free up resources
- Use the proxy server for multiple projects
- Monitor console for performance issues

### Workflow
1. **Create** projects with auto-domain setup
2. **Build** projects before first start
3. **Start** proxy server for HTTPS access
4. **Start** individual projects as needed
5. **Monitor** console for status updates

## 📚 Related Documentation

- [LPES Main Documentation](README.md)
- [Command Examples](COMMAND_EXAMPLES.md)
- [Project Management Guide](PROJECT_MANAGEMENT_GUIDE.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

## 🤝 Support

If you encounter issues with the GUI:
1. Check the integrated console for error messages
2. Export and review log files
3. Verify LPES CLI commands work manually
4. Check system requirements and permissions

---

**No more command line hassles! Manage your LPES projects with style. 🚀**
