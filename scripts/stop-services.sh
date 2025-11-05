#!/bin/bash

# Stop all services for Strands Autonomous Platform

echo "🛑 Stopping Strands Autonomous Platform Services..."
echo "=================================================="

# Stop services
docker-compose down

echo ""
echo "✅ All services stopped"
echo ""
echo "To remove all data: docker-compose down -v"
echo ""
