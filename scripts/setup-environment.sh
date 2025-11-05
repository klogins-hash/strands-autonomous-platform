#!/bin/bash

# Complete environment setup for Strands Autonomous Platform

echo "🚀 Setting up Strands Autonomous Platform Environment"
echo "======================================================"

# Step 1: Check/Install Docker
echo ""
echo "Step 1: Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Installing..."
    ./scripts/install-docker.sh
else
    echo "✅ Docker is installed"
fi

# Step 2: Check if Colima is running
echo ""
echo "Step 2: Checking Docker runtime..."
if ! docker info &> /dev/null; then
    echo "⚠️  Docker runtime not running. Starting Colima..."
    
    if command -v colima &> /dev/null; then
        colima start --cpu 4 --memory 8 --disk 50
    else
        echo "❌ Colima not installed. Installing..."
        brew install colima
        colima start --cpu 4 --memory 8 --disk 50
    fi
else
    echo "✅ Docker runtime is running"
fi

# Step 3: Install Python dependencies
echo ""
echo "Step 3: Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Python dependencies installed"
else
    echo "⚠️  requirements.txt not found"
fi

# Step 4: Create .env if it doesn't exist
echo ""
echo "Step 4: Checking environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env from .env.example"
        echo "⚠️  Please update .env with your API keys"
    else
        echo "⚠️  .env.example not found"
    fi
else
    echo "✅ .env file exists"
fi

# Step 5: Start services
echo ""
echo "Step 5: Starting services..."
./scripts/start-services.sh

echo ""
echo "======================================================"
echo "✨ Environment setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Update .env with your API keys (if not done)"
echo "   2. Run: python main.py"
echo ""
echo "======================================================"
