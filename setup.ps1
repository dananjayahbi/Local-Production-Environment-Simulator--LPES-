# LPES Quick Setup Script for PowerShell
# Usage: .\setup.ps1 -ProjectName "my-app" -ProjectPath "E:\Test_files\next_temp_pr"

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectName,
    
    [Parameter(Mandatory=$true)]
    [string]$ProjectPath,
    
    [string]$Domain = "$ProjectName.local",
    [string]$BuildCommand = "npm run build",
    [string]$StartCommand = "npm start",
    [int]$Port = 3000,
    [switch]$StartAfterSetup
)

# Colors for output
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"
$White = "White"

Write-Host "🚀 LPES Quick Setup Starting..." -ForegroundColor $Green
Write-Host "Project: $ProjectName" -ForegroundColor $White
Write-Host "Path: $ProjectPath" -ForegroundColor $White
Write-Host "Domain: $Domain" -ForegroundColor $White
Write-Host "Port: $Port" -ForegroundColor $White
Write-Host ""

# Function to check command success
function Test-CommandSuccess {
    param([string]$CommandName)
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ $CommandName completed successfully!" -ForegroundColor $Green
        return $true
    } else {
        Write-Host "❌ $CommandName failed! Exit code: $LASTEXITCODE" -ForegroundColor $Red
        return $false
    }
}

# Step 1: Initialize project
Write-Host "📝 Step 1: Initializing project..." -ForegroundColor $Yellow
$initCmd = "python main.py init `"$ProjectName`" --path `"$ProjectPath`" --build `"$BuildCommand`" --start `"$StartCommand`" --port $Port"
Write-Host "Command: $initCmd" -ForegroundColor $White
Invoke-Expression $initCmd

if (Test-CommandSuccess "Project initialization") {
    
    # Step 2: Add domain
    Write-Host "`n🌐 Step 2: Adding domain and SSL..." -ForegroundColor $Yellow
    $domainCmd = "python main.py domain add `"$ProjectName`" `"$Domain`" --ssl --hosts-file"
    Write-Host "Command: $domainCmd" -ForegroundColor $White
    Invoke-Expression $domainCmd
    
    if (Test-CommandSuccess "Domain addition") {
        
        # Step 3: Build project
        Write-Host "`n🔨 Step 3: Building project..." -ForegroundColor $Yellow
        $buildCmd = "python main.py build `"$ProjectName`""
        Write-Host "Command: $buildCmd" -ForegroundColor $White
        Invoke-Expression $buildCmd
        
        if (Test-CommandSuccess "Project build") {
            
            Write-Host "`n🎉 Setup completed successfully!" -ForegroundColor $Green
            Write-Host ""
            Write-Host "📋 Next steps:" -ForegroundColor $Cyan
            Write-Host "  1. Start your project:" -ForegroundColor $White
            Write-Host "     python main.py start `"$ProjectName`"" -ForegroundColor $Yellow
            Write-Host ""
            Write-Host "  2. Start the HTTPS proxy:" -ForegroundColor $White
            Write-Host "     python main.py proxy start" -ForegroundColor $Yellow
            Write-Host ""
            Write-Host "  3. Access your app at:" -ForegroundColor $White
            Write-Host "     https://$Domain" -ForegroundColor $Cyan
            Write-Host ""
            
            if ($StartAfterSetup) {
                Write-Host "🚀 Auto-starting project and proxy..." -ForegroundColor $Green
                
                # Start project in background
                Write-Host "Starting project..." -ForegroundColor $Yellow
                Start-Process -NoNewWindow -FilePath "python" -ArgumentList "main.py", "start", $ProjectName
                Start-Sleep 3
                
                # Start proxy
                Write-Host "Starting proxy..." -ForegroundColor $Yellow
                Write-Host "Note: Proxy will run in foreground. Press Ctrl+C to stop." -ForegroundColor $Yellow
                python main.py proxy start
            } else {
                Write-Host "💡 Tip: Use -StartAfterSetup flag to automatically start after setup" -ForegroundColor $Cyan
            }
            
        } else {
            Write-Host "`n❌ Build failed. Check your build command and project path." -ForegroundColor $Red
        }
    } else {
        Write-Host "`n❌ Domain addition failed. You may need to run as Administrator for hosts file modification." -ForegroundColor $Red
    }
} else {
    Write-Host "`n❌ Project initialization failed. Check your project path and permissions." -ForegroundColor $Red
}

Write-Host "`n📚 For more help, run: python main.py --help" -ForegroundColor $Cyan
