# LPES Project Management Guide

## 📋 Project Operations

### 1. List All Projects
```powershell
python main.py list
```

### 2. Check Project Details
```powershell
# List domains for a specific project
python main.py domain list simpleapp

# Check SSL certificates
python main.py ssl list
```

### 3. Delete Projects

#### Basic Removal (Keeps SSL & Domains)
```powershell
python main.py remove my-app
```

#### Complete Cleanup (Removes Everything)
```powershell
python main.py remove simpleapp --cleanup
```

**What `--cleanup` does:**
- ✅ Stops the project if running
- ✅ Revokes SSL certificates
- ✅ Removes domains from hosts file
- ✅ Deletes project configuration
- ✅ Cleans up all associated files

### 4. Batch Operations

#### Remove Multiple Projects
```powershell
# Remove projects one by one
python main.py remove my-app --cleanup
python main.py remove simpleapp --cleanup
python main.py remove test-app --cleanup
```

#### Check Before Removing
```powershell
# Always list first to see what exists
python main.py list

# Then remove specific projects
python main.py remove project-name --cleanup
```

## 🔍 Troubleshooting

### Problem: "Project not found" Error
```
ERROR - Project simpleapp not found
```

**Solution 1**: Check if project exists
```powershell
python main.py list
```

**Solution 2**: Create the project first
```powershell
python main.py init simpleapp --path "E:\path\to\project" --build "npm run build" --start "npm start" --port 3000
```

**Solution 3**: Use correct project name
```powershell
# Wrong (if project is called 'my-app')
python main.py domain add simpleapp simpleapp.local --ssl

# Correct
python main.py domain add my-app simpleapp.local --ssl
```

### Problem: Permission Denied (Hosts File)
```
Permission denied: Cannot modify hosts file
```

**Solution**: Run PowerShell as Administrator
1. Right-click PowerShell
2. Select "Run as Administrator"
3. Navigate to LPES directory
4. Run the command again

### Problem: SSL Certificate Issues
**Check Certificates:**
```powershell
python main.py ssl list
```

**Generate New Certificate:**
```powershell
python main.py ssl generate domain.local
```

**Get Trust Instructions:**
```powershell
python main.py ssl trust-info
```

## 📚 Quick Reference

### Project Lifecycle
```powershell
# 1. Create
python main.py init myproject --path "C:\path" --build "npm run build" --start "npm start" --port 3000

# 2. Add Domain
python main.py domain add myproject myproject.local --ssl --hosts-file

# 3. Build
python main.py build myproject

# 4. Start
python main.py start myproject

# 5. Use (in browser)
# https://myproject.local

# 6. Stop
python main.py stop myproject

# 7. Remove
python main.py remove myproject --cleanup
```

### Domain Management
```powershell
# List all domains
python main.py domain list myproject

# Add additional domain
python main.py domain add myproject api.myproject.local --ssl

# Remove domain (manual SSL cleanup needed)
python main.py domain remove myproject api.myproject.local
```

### Proxy Management
```powershell
# Start proxy (required for HTTPS)
python main.py proxy start

# Stop proxy
python main.py proxy stop

# Custom port
python main.py proxy start --port 8443
```

## ⚠️ Important Notes

1. **Always use `--cleanup`** when removing projects to avoid leftover files
2. **Run as Administrator** for hosts file modifications
3. **Stop projects** before removing them
4. **List projects first** to verify names before operations
5. **Use quotes** for paths with spaces: `"E:\My Projects\app"`

## 🔄 Current Status

Based on your current setup:

**Existing Projects:**
- ✅ `my-app` (domain: simpleapp.local)
- ✅ `simpleapp` (domain: simpleapp.local) 

**Next Steps:**
1. Choose which project to keep (both have same domain)
2. Remove duplicate project:
   ```powershell
   python main.py remove my-app --cleanup
   ```
3. Or rename domain for one of them:
   ```powershell
   python main.py domain add my-app myapp.local --ssl --hosts-file
   ```

## 🛠️ Recommended Cleanup

Since you have duplicate domain configurations, I recommend:

```powershell
# Keep simpleapp, remove my-app
python main.py remove my-app --cleanup

# Or keep my-app, remove simpleapp
python main.py remove simpleapp --cleanup

# Verify cleanup
python main.py list
```
