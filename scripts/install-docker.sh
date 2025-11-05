#!/bin/bash

# Install Docker on macOS using Homebrew (no Docker Desktop needed)

echo "🐳 Installing Docker via Homebrew..."
echo "=================================================="

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew is not installed. Installing Homebrew first..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

echo ""
echo "📦 Installing Docker..."
brew install docker docker-compose

echo ""
echo "📦 Installing Colima (Docker runtime)..."
brew install colima

echo ""
echo "🚀 Starting Colima..."
colima start --cpu 4 --memory 8 --disk 50

echo ""
echo "✅ Docker installation complete!"
echo ""
echo "=================================================="
echo "📊 Docker Info:"
docker version
echo ""
echo "=================================================="
echo ""
echo "💡 Useful commands:"
echo "   Start Docker: colima start"
echo "   Stop Docker: colima stop"
echo "   Check status: colima status"
echo "   Docker info: docker info"
echo ""
