#!/usr/bin/env bash
# ============================================================
# EQ Tools Suite Environment Setup (Linux/macOS)
#
# Usage:
#   chmod +x setup_environment.sh
#   ./setup_environment.sh
#
# Requirements:
#   • Python 3.11+ (ideally 3.13)
#   • pip & venv included
# ============================================================

set -e
echo "Setting up EQ Tools Suite development environment..."

python -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Virtual environment setup complete!"
echo "To activate later: source venv/bin/activate"
echo "To run the app:    python main_window.py"
