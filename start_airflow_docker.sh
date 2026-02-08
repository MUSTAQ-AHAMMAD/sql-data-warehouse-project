#!/bin/bash

echo "🐳 Starting Airflow with Docker..."
echo ""

cd /c/xampp/htdocs/sql-data-warehouse-project

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "Please start Docker Desktop first."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Initialize Airflow (first time only)
if [ ! -f ".airflow_initialized" ]; then
    echo "📦 Initializing Airflow (first time)..."
    docker-compose up airflow-init
    touch .airflow_initialized
    echo ""
fi

# Start services
echo "🚀 Starting Airflow services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check status
docker-compose ps

echo ""
echo "="*60
echo "✅ Airflow is running!"
echo ""
echo "🌐 Web UI: http://localhost:8080"
echo "👤 Username: admin"
echo "🔑 Password: admin123"
echo ""
echo "📊 View logs: docker-compose logs -f"
echo "🛑 Stop: docker-compose down"
echo "="*60
