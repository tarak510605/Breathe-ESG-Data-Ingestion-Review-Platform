#!/bin/bash
# Quick start script for Breathe ESG

set -e

echo "🌍 Breathe ESG - Quick Start"
echo "============================"
echo ""

# Check if docker is available
if command -v docker &> /dev/null; then
    echo "✅ Docker detected - Using Docker Compose"
    echo ""
    echo "Starting services..."
    docker-compose up -d
    echo ""
    echo "Waiting for services to be ready..."
    sleep 5
    echo ""
    echo "Loading seed data..."
    docker-compose exec -T backend python manage.py migrate > /dev/null 2>&1
    docker-compose exec -T backend python manage.py shell < manage_commands/seed_data.py > /dev/null 2>&1
    echo ""
    echo "✅ Services started!"
    echo ""
    echo "Access the application:"
    echo "  Frontend: http://localhost:3000"
    echo "  API: http://localhost:8000/api"
    echo "  Admin: http://localhost:8000/admin"
    echo ""
    echo "Login with:"
    echo "  Email: analyst@example.com"
    echo "  Password: testpass123"
    echo ""
    echo "View logs with:"
    echo "  docker-compose logs -f backend"
    echo "  docker-compose logs -f frontend"
    echo ""
    echo "Stop with:"
    echo "  docker-compose down"
    
else
    echo "Docker not found - Manual setup required"
    echo ""
    echo "Backend setup:"
    echo "  cd backend"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo "  cp .env.example .env"
    echo "  python manage.py migrate"
    echo "  python manage.py shell < manage_commands/seed_data.py"
    echo "  python manage.py runserver"
    echo ""
    echo "Frontend setup (new terminal):"
    echo "  cd frontend"
    echo "  npm install"
    echo "  npm run dev"
    echo ""
    echo "Then visit http://localhost:3000"
fi
