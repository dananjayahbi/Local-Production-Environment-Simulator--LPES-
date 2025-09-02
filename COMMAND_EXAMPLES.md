# LPES Command Examples for Different Shells

## PowerShell (Windows)

### Single Line Commands (Recommended)
```powershell
# Initialize project
python main.py init my-app --path "E:\Test_files\next_temp_pr" --build "npm run build" --start "npm start" --port 3000

# Add domain
python main.py domain add my-app myapp.local --ssl --hosts-file

# Build project
python main.py build my-app

# Start project
python main.py start my-app

# Start proxy
python main.py proxy start
```

### Multi-line Commands (PowerShell)
```powershell
# Use backticks for line continuation in PowerShell
python main.py init my-app `
  --path "E:\Test_files\next_temp_pr" `
  --build "npm run build" `
  --start "npm start" `
  --port 3000
```

## Bash/Command Prompt (Linux/macOS/WSL)

### Multi-line Commands
```bash
# Use backslashes for line continuation in Bash
python main.py init my-app \
  --path "/path/to/project" \
  --build "npm run build" \
  --start "npm start" \
  --port 3000
```

## Batch File (Windows .bat)

### Create a batch file for easy setup
```batch
@echo off
echo Setting up LPES project...

python main.py init my-app --path "E:\Test_files\next_temp_pr" --build "npm run build" --start "npm start" --port 3000
python main.py domain add my-app myapp.local --ssl --hosts-file
python main.py build my-app
python main.py start my-app

echo Project setup complete!
echo Starting proxy server...
python main.py proxy start
```

## Quick Setup Script

### Windows PowerShell Script (setup.ps1)
```powershell
# LPES Quick Setup Script
param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectName,
    
    [Parameter(Mandatory=$true)]
    [string]$ProjectPath,
    
    [string]$Domain = "$ProjectName.local",
    [string]$BuildCommand = "npm run build",
    [string]$StartCommand = "npm start",
    [int]$Port = 3000
)

Write-Host "🚀 Setting up LPES project: $ProjectName" -ForegroundColor Green

# Initialize project
Write-Host "📝 Initializing project..." -ForegroundColor Yellow
python main.py init $ProjectName --path $ProjectPath --build $BuildCommand --start $StartCommand --port $Port

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Project initialized successfully!" -ForegroundColor Green
    
    # Add domain
    Write-Host "🌐 Adding domain: $Domain" -ForegroundColor Yellow
    python main.py domain add $ProjectName $Domain --ssl --hosts-file
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Domain added successfully!" -ForegroundColor Green
        
        # Build project
        Write-Host "🔨 Building project..." -ForegroundColor Yellow
        python main.py build $ProjectName
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Build completed successfully!" -ForegroundColor Green
            Write-Host "📋 Setup complete! Next steps:" -ForegroundColor Cyan
            Write-Host "  1. Start project: python main.py start $ProjectName" -ForegroundColor White
            Write-Host "  2. Start proxy: python main.py proxy start" -ForegroundColor White
            Write-Host "  3. Access via: https://$Domain" -ForegroundColor White
        } else {
            Write-Host "❌ Build failed!" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ Failed to add domain!" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Failed to initialize project!" -ForegroundColor Red
}
```

### Usage of PowerShell Script
```powershell
# Save the script as setup.ps1, then run:
.\setup.ps1 -ProjectName "my-app" -ProjectPath "E:\Test_files\next_temp_pr"

# Or with custom domain:
.\setup.ps1 -ProjectName "my-app" -ProjectPath "E:\Test_files\next_temp_pr" -Domain "myawesome.local"
```

## Common Issues and Solutions

### Issue 1: Line Continuation Errors
**Problem**: `Error: Got unexpected extra arguments (\ \ \ \)`

**Solution**: Use correct line continuation for your shell:
- PowerShell: Use backticks `` ` ``
- Bash: Use backslashes `\`
- Or use single line commands

### Issue 2: Path with Spaces
**Problem**: Paths with spaces cause argument parsing errors

**Solution**: Always quote paths:
```powershell
# Correct
python main.py init my-app --path "E:\Test files\my project"

# Wrong
python main.py init my-app --path E:\Test files\my project
```

### Issue 3: Permission Errors
**Problem**: Cannot modify hosts file or bind to port 443

**Solution**: Run PowerShell as Administrator:
```powershell
# Run PowerShell as Administrator, then:
python main.py domain add my-app myapp.local --ssl --hosts-file
python main.py proxy start
```

### Issue 4: Special Characters in Commands
**Problem**: Build/start commands with special characters fail

**Solution**: Properly escape or quote commands:
```powershell
# For complex commands, use single quotes
python main.py init my-app --path "C:\project" --build 'npm run build && echo "Build complete"' --start "npm start"
```

## Environment-Specific Examples

### NextJS Project
```powershell
python main.py init nextjs-app --path "E:\projects\my-nextjs-app" --build "npm run build" --start "npm start" --port 3000
```

### Vite Project
```powershell
python main.py init vite-app --path "E:\projects\my-vite-app" --build "npm run build" --start "npm run preview" --port 4173
```

### Custom Port
```powershell
python main.py init custom-app --path "E:\projects\app" --build "npm run build" --start "npm start" --port 8080
```

## Testing Your Setup

### Test Commands
```powershell
# 1. Test LPES installation
python main.py --help

# 2. List projects (should be empty initially)
python main.py list

# 3. Initialize test project
python main.py init test-app --path "E:\Test_files\next_temp_pr" --build "echo 'test build'" --start "echo 'test start'" --port 3000

# 4. Verify project was created
python main.py list

# 5. Clean up test
python main.py remove test-app --cleanup
```
