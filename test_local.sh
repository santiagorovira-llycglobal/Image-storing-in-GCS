#!/bin/bash

# Local Testing Script for Image Storage Cloud Function
# This script starts a local server using Functions Framework

set -e  # Exit on error

echo "=========================================="
echo "Local Image Storage Function Server"
echo "=========================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please copy .env.example to .env and configure it:"
    echo "  cp .env.example .env"
    exit 1
fi

# Load environment variables from .env
echo "✓ Loading environment variables from .env"
export $(cat .env | grep -v '^#' | xargs)

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✓ Activating virtual environment"
source venv/bin/activate

# Install dependencies
echo "✓ Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "=========================================="
echo "Starting Local Server"
echo "=========================================="
echo ""
echo "Function: procesar_imagenes_sheet"
echo "URL: http://localhost:8080"
echo ""
echo "To test, run in another terminal:"
echo "  curl -X POST http://localhost:8080"
echo ""
echo "Or open in browser:"
echo "  http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Start the Functions Framework server
functions-framework --target=procesar_imagenes_sheet --debug --port=8080
