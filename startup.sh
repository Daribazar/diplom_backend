#!/bin/bash

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        AI Study Assistant - System Startup Check          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Check PostgreSQL
echo "1️⃣  Checking PostgreSQL..."
if psql -U postgres -d study_assistant -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL running${NC}"
else
    echo -e "${RED}❌ PostgreSQL not running${NC}"
    echo "   Starting PostgreSQL..."
    brew services start postgresql
    sleep 3
    if psql -U postgres -d study_assistant -c "SELECT 1;" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PostgreSQL started${NC}"
    else
        echo -e "${RED}❌ Failed to start PostgreSQL${NC}"
    fi
fi

# 2. Check Redis
echo ""
echo "2️⃣  Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis running${NC}"
else
    echo -e "${RED}❌ Redis not running${NC}"
    echo "   Starting Redis..."
    brew services start redis
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis started${NC}"
    else
        echo -e "${RED}❌ Failed to start Redis${NC}"
    fi
fi

# 3. Check Virtual Environment
echo ""
echo "3️⃣  Checking Virtual Environment..."
if [ -d "venv" ]; then
    echo -e "${GREEN}✅ Virtual environment exists${NC}"
else
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo "   Create with: python3 -m venv venv"
fi

# 4. Check FastAPI
echo ""
echo "4️⃣  Checking FastAPI Server..."
if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ FastAPI running on port 8000${NC}"
    
    # Get health status
    HEALTH=$(curl -s http://127.0.0.1:8000/health)
    echo "   Status: $(echo $HEALTH | jq -r '.status')"
    echo "   Database: $(echo $HEALTH | jq -r '.database')"
    echo "   Redis: $(echo $HEALTH | jq -r '.redis')"
else
    echo -e "${YELLOW}⚠️  FastAPI not running${NC}"
    echo "   Start with:"
    echo "   ${YELLOW}source venv/bin/activate${NC}"
    echo "   ${YELLOW}uvicorn src.main:app --reload --port 8000${NC}"
fi

# 5. Check Celery
echo ""
echo "5️⃣  Checking Celery Worker..."
if pgrep -f "celery.*worker" > /dev/null; then
    echo -e "${GREEN}✅ Celery worker running${NC}"
    CELERY_PID=$(pgrep -f "celery.*worker")
    echo "   PID: $CELERY_PID"
else
    echo -e "${YELLOW}⚠️  Celery worker not running${NC}"
    echo "   Start with:"
    echo "   ${YELLOW}source venv/bin/activate${NC}"
    echo "   ${YELLOW}celery -A src.infrastructure.queue.celery_app worker --loglevel=info${NC}"
fi

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    QUICK START COMMANDS                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Terminal 1 (FastAPI):"
echo "  cd ~/Documents/diplom/study-assistant-backend"
echo "  source venv/bin/activate"
echo "  uvicorn src.main:app --reload --port 8000"
echo ""
echo "Terminal 2 (Celery):"
echo "  cd ~/Documents/diplom/study-assistant-backend"
echo "  source venv/bin/activate"
echo "  celery -A src.infrastructure.queue.celery_app worker --loglevel=info"
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                       USEFUL LINKS                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📖 API Documentation: http://127.0.0.1:8000/api/docs"
echo "🔍 Health Check:      http://127.0.0.1:8000/health"
echo "🏠 Root:              http://127.0.0.1:8000/"
echo ""
