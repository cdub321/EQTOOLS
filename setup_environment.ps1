# ============================================================
# EQ Tools Suite Environment Setup (Windows PowerShell)
#
# Usage:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\setup_environment.ps1
#
# Requirements:
#   • Python 3.11+ (ideally 3.13)
#   • pip & venv included
# ============================================================

Write-Host "Setting up EQ Tools Suite development environment..."

python -m venv venv
.\venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host ""
Write-Host "Virtual environment setup complete!"
Write-Host "To activate later: .\venv\Scripts\activate"
Write-Host "To run the app:    python main_window.py"
