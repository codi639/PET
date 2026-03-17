#
# PET - Personal Encryption Tool - Windows Registry Context Menu Setup
# Adds "Encrypt with PET" and "Decrypt with PET" options to Windows Explorer context menu
#

param(
    [switch]$Uninstall
)

# Color function for output
function Write-Status {
    param([string]$Message, [string]$Status)
    $color = if ($Status -eq "Success") { "Green" } elseif ($Status -eq "Error") { "Red" } else { "Yellow" }
    Write-Host $Message -ForegroundColor $color
}

# Set error action preference
$ErrorActionPreference = "Stop"

try {
    # Get script directory
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

    # Find Python executable
    $pythonPath = $null
    $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $pythonPath) {
        $pythonPath = (Get-Command python3 -ErrorAction SilentlyContinue).Source
    }

    if (-not $pythonPath) {
        Write-Status "Error: Python not found. Please install Python and add it to PATH." "Error"
        exit 1
    }

    # Find pet.py (main entry point)
    #$petPath = Join-Path $scriptDir "interface\gui_tray.py"
    $petPath = Join-Path $scriptDir "pet.py"
    if (-not (Test-Path $petPath)) {
        Write-Status "Error: pet.py not found at $petPath" "Error"
        exit 1
    }

    # Registry base path - using Software\Classes for context menus
    #$regBase = "HKCU:\Software\Classes"
    $regBase = "HKCU:"

    if ($Uninstall) {
        Write-Status "`nUninstalling PET Context Menus..." "Warning"
        Write-Host "========================================="

        # Remove Encrypt from all files (*\shell)
        $encryptPath = "$regBase\*\shell\PETCMD_Encrypt"
        if (Test-Path $encryptPath) {
            Remove-Item -Path $encryptPath -Recurse -Force -ErrorAction SilentlyContinue
            Write-Status "Removed: Encrypt with PET" "Success"
        }

        # Remove Decrypt from .pet files
        $decryptPath = "$regBase\.pet\shell\PETCMD_Decrypt"
        if (Test-Path $decryptPath) {
            Remove-Item -Path $decryptPath -Recurse -Force -ErrorAction SilentlyContinue
            Write-Status "Removed: Decrypt with PET" "Success"
        }

        Write-Host "`n========================================="
        Write-Status "PET Context Menus uninstalled!" "Success"
        exit 0
    }

    # Installation
    Write-Status "`nPET Context Menu Setup" "Warning"
    Write-Host "========================================="
    Write-Host "`nPython: $pythonPath"
    Write-Host "Script: $petPath`n"

    # Create * (all files) shell key if needed
    $allFilesPath = "$regBase\*\shell"
    if (-not (Test-Path $allFilesPath)) {
        New-Item -Path $allFilesPath -Force | Out-Null
    }

    # Add Encrypt option
    $encryptPath = "$allFilesPath\PETCMD_Encrypt"
    New-Item -Path $encryptPath -Force | Out-Null
    New-ItemProperty -Path $encryptPath -Name "(Default)" -Value "Encrypt with PET" -Force | Out-Null

    $encryptCmd = "$encryptPath\command"
    New-Item -Path $encryptCmd -Force | Out-Null
    $encryptCommand = "`"$pythonPath`" `"$petPath`" --encrypt `"%1`""
    New-ItemProperty -Path $encryptCmd -Name "(Default)" -Value $encryptCommand -Force | Out-Null
    Write-Status "Added: Encrypt with PET" "Success"

    # Create .pet files shell key if needed
    $petFilesPath = "$regBase\.pet\shell"
    if (-not (Test-Path $petFilesPath)) {
        New-Item -Path $petFilesPath -Force | Out-Null
    }

    # Add Decrypt option
    $decryptPath = "$petFilesPath\PETCMD_Decrypt"
    New-Item -Path $decryptPath -Force | Out-Null
    New-ItemProperty -Path $decryptPath -Name "(Default)" -Value "Decrypt with PET" -Force | Out-Null

    $decryptCmd = "$decryptPath\command"
    New-Item -Path $decryptCmd -Force | Out-Null
    $decryptCommand = "`"$pythonPath`" `"$petPath`" --decrypt `"%1`""
    New-ItemProperty -Path $decryptCmd -Name "(Default)" -Value $decryptCommand -Force | Out-Null
    Write-Status "Added: Decrypt with PET" "Success"

    Write-Host "`n========================================="
    Write-Status "Setup completed successfully!" "Success"
    Write-Host "`nYou can now:"
    Write-Host "  Right-click any file -> Encrypt with PET"
    Write-Host "  Right-click .pet files -> Decrypt with PET"
    Write-Host "`nTo uninstall: powershell -ExecutionPolicy Bypass -File setup_registry.ps1 -Uninstall"
    Write-Host ""
    exit 0
}
catch {
    Write-Status "`nError: $($_.Exception.Message)" "Error"
    exit 1
}
