#!/bin/bash

# Start all required services for Strands Autonomous Platform

echo "🚀 Starting Strands Autonomous Platform Services..."
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running."
    echo ""
    echo "Starting Colima (Docker runtime)..."
    
    if command -v colima &> /dev/null; then
        colima start --cpu 4 --memory 8 --disk 50
        sleep 5
    else
        echo "❌ Colima not installed. Please run: ./scripts/install-docker.sh"
        exit 1
    fi
fi

# Start services with docker-compose
echo ""
echo "📦 Starting PostgreSQL, Redis, and MinIO..."
docker-compose up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check PostgreSQL
echo "🔍 Checking PostgreSQL..."
until docker exec strands-postgres pg_isready -U strands > /dev/null 2>&1; do
    echo "   Waiting for PostgreSQL..."
    sleep 2
done
echo "✅ PostgreSQL is ready"

# Check Redis
echo "🔍 Checking Redis..."
until docker exec strands-redis redis-cli ping > /dev/null 2>&1; do
    echo "   Waiting for Redis..."
    sleep 2
done
echo "✅ Redis is ready"

# Check MinIO
echo "🔍 Checking MinIO..."
until curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; do
    echo "   Waiting for MinIO..."
    sleep 2
done
echo "✅ MinIO is ready"

echo ""
echo "=================================================="
echo "✨ All services are running!"
echo ""
echo "📊 Service URLs:"
echo "   PostgreSQL: localhost:5432"
echo "   Redis: localhost:6379"
echo "   MinIO API: http://localhost:9000"
echo "   MinIO Console: http://localhost:9001"
echo ""
echo "🔐 MinIO Credentials:"
echo "   Username: minioadmin"
echo "   Password: minioadmin"
echo ""
echo "📝 Database Connection:"
echo "   postgresql://strands:strands_password@localhost:5432/strands_platform"
echo ""
echo "=================================================="
echo ""
echo "To stop services: docker-compose down"
echo "To view logs: docker-compose logs -f"
echo ""
