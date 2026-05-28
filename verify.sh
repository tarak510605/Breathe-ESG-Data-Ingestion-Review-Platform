#!/bin/bash
# Verify Breathe ESG installation and setup

set -e

echo "🌍 Breathe ESG - Installation Verification"
echo "==========================================="
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ $PYTHON_VERSION"
else
    echo "❌ Python 3 not found"
    exit 1
fi

# Check Node
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node $NODE_VERSION"
else
    echo "❌ Node not found"
    exit 1
fi

# Check PostgreSQL
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL installed"
else
    echo "⚠️  PostgreSQL not found (required for production)"
fi

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "✅ $DOCKER_VERSION"
else
    echo "⚠️  Docker not found (optional)"
fi

echo ""
echo "Backend Setup"
echo "============="
cd backend

# Check Python dependencies
if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt found"
    pip_count=$(wc -l < requirements.txt)
    echo "   Dependencies: $pip_count packages"
else
    echo "❌ requirements.txt not found"
    exit 1
fi

# Check Django apps
for app in breathe organizations data_sources ingestion emissions audit; do
    if [ -d "$app" ]; then
        echo "✅ $app app exists"
    else
        echo "❌ $app app missing"
        exit 1
    fi
done

# Check models
for model in breathe organizations data_sources ingestion emissions audit; do
    if [ -f "$model/models.py" ]; then
        echo "✅ $model/models.py exists"
    else
        echo "❌ $model/models.py missing"
        exit 1
    fi
done

# Check settings
if [ -f "breathe/settings.py" ]; then
    echo "✅ Django settings configured"
else
    echo "❌ Django settings missing"
    exit 1
fi

echo ""
echo "Frontend Setup"
echo "=============="
cd ../frontend

# Check Node dependencies
if [ -f "package.json" ]; then
    echo "✅ package.json found"
    npm_count=$(grep -c '"' package.json || echo "0")
    echo "   Dependencies listed in package.json"
else
    echo "❌ package.json not found"
    exit 1
fi

# Check React files
for file in src/index.tsx src/App.tsx src/api/client.ts vite.config.ts tsconfig.json; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

echo ""
echo "Documentation"
echo "=============="
cd ..

for doc in README.md DEPLOYMENT.md GETTING_STARTED.md ARCHITECTURE.md DECISIONS.md TRADEOFFS.md; do
    if [ -f "$doc" ]; then
        echo "✅ $doc exists"
    else
        echo "⚠️  $doc missing (optional)"
    fi
done

echo ""
echo "Configuration Files"
echo "==================="
for file in docker-compose.yml Dockerfile render.yaml .github/workflows/ci.yml; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "⚠️  $file missing (optional)"
    fi
done

echo ""
echo "✅ Installation verification complete!"
echo ""
echo "Next steps:"
echo "1. cd backend && python -m venv venv"
echo "2. source venv/bin/activate"
echo "3. pip install -r requirements.txt"
echo "4. cp .env.example .env"
echo "5. python manage.py migrate"
echo "6. python manage.py shell < manage_commands/seed_data.py"
echo "7. cd ../frontend && npm install && npm run dev"
echo ""
echo "Then visit http://localhost:3000"
