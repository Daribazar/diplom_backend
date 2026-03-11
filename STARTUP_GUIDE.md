# 🚀 AI Study Assistant - Системийг Эхлүүлэх Заавар

Компьютер унтраагаад дахин асаахад дараах дарааллаар системийг эхлүүлнэ.

---

## 📋 Шаардлагатай Зүйлс

Эдгээр нь аль хэдийн суусан байх ёстой:
- ✅ Python 3.9+
- ✅ PostgreSQL 18
- ✅ Redis
- ✅ Virtual Environment (venv)

---

## 🔧 1. Terminal Нээх

```bash
# Project folder руу очих
cd ~/Documents/diplom/study-assistant-backend
```

---

## 🗄️ 2. PostgreSQL Эхлүүлэх

### macOS (Homebrew):
```bash
# PostgreSQL статус шалгах
brew services list | grep postgresql

# Хэрэв зогссон бол эхлүүлэх
brew services start postgresql@18

# Эсвэл зөвхөн PostgreSQL
brew services start postgresql
```

### Шалгах:
```bash
psql -U postgres -d study_assistant -c "SELECT 1;"
```

Амжилттай бол `1` гэж харагдана.

---

## 🔴 3. Redis Эхлүүлэх

### macOS (Homebrew):
```bash
# Redis статус шалгах
brew services list | grep redis

# Хэрэв зогссон бол эхлүүлэх
brew services start redis
```

### Шалгах:
```bash
redis-cli ping
```

Амжилттай бол `PONG` гэж харагдана.

---

## 🐍 4. Virtual Environment Идэвхжүүлэх

```bash
# Project folder-д байгаа эсэхийг шалгах
pwd
# Үр дүн: /Users/daribazar/Documents/diplom/study-assistant-backend

# Virtual environment идэвхжүүлэх
source venv/bin/activate

# Идэвхжсэн эсэхийг шалгах (prompt-д (venv) гэж харагдана)
which python
# Үр дүн: /Users/daribazar/Documents/diplom/study-assistant-backend/venv/bin/python
```

---

## 🌐 5. FastAPI Server Эхлүүлэх

### Terminal 1 (FastAPI):
```bash
# Virtual environment идэвхжүүлсэн байх ёстой
source venv/bin/activate

# FastAPI server эхлүүлэх
uvicorn src.main:app --reload --port 8000
```

**Амжилттай бол:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete.
```

**Шалгах:**
```bash
# Өөр terminal нээгээд
curl http://127.0.0.1:8000/health
```

Үр дүн:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

---

## ⚙️ 6. Celery Worker Эхлүүлэх

### Terminal 2 (Celery):
```bash
# Шинэ terminal нээх
cd ~/Documents/diplom/study-assistant-backend

# Virtual environment идэвхжүүлэх
source venv/bin/activate

# Celery worker эхлүүлэх
celery -A src.infrastructure.queue.celery_app worker --loglevel=info
```

**Амжилттай бол:**
```
[tasks]
  . lecture_processing.process_lecture
  . lecture_processing.test_task

celery@YourMacBook.local ready.
```

---

## ✅ 7. Систем Бэлэн Эсэхийг Шалгах

### Бүх сервисүүдийг шалгах:
```bash
# Health check
curl http://127.0.0.1:8000/health | jq '.'

# API Documentation
open http://127.0.0.1:8000/api/docs
```

### Эсвэл test script ашиглах:
```bash
source venv/bin/activate
python scripts/test_db_connection.py
```

---

## 🎯 Бүрэн Эхлүүлэх Скрипт

Нэг командаар бүгдийг шалгах:

```bash
#!/bin/bash
# startup.sh

echo "🚀 Starting AI Study Assistant..."
echo ""

# 1. Check PostgreSQL
echo "1️⃣  Checking PostgreSQL..."
if psql -U postgres -d study_assistant -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ PostgreSQL running"
else
    echo "❌ PostgreSQL not running. Starting..."
    brew services start postgresql
    sleep 2
fi

# 2. Check Redis
echo ""
echo "2️⃣  Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis running"
else
    echo "❌ Redis not running. Starting..."
    brew services start redis
    sleep 2
fi

# 3. Check FastAPI
echo ""
echo "3️⃣  Checking FastAPI..."
if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "✅ FastAPI running"
else
    echo "⚠️  FastAPI not running"
    echo "   Start with: uvicorn src.main:app --reload --port 8000"
fi

# 4. Check Celery
echo ""
echo "4️⃣  Checking Celery..."
if pgrep -f "celery.*worker" > /dev/null; then
    echo "✅ Celery running"
else
    echo "⚠️  Celery not running"
    echo "   Start with: celery -A src.infrastructure.queue.celery_app worker --loglevel=info"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    SYSTEM STATUS                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📖 API Docs:  http://127.0.0.1:8000/api/docs"
echo "🔍 Health:    http://127.0.0.1:8000/health"
echo ""
```

**Ашиглах:**
```bash
chmod +x startup.sh
./startup.sh
```

---

## 🛑 Системийг Зогсоох

### FastAPI зогсоох:
```
Terminal 1-д: Ctrl + C
```

### Celery зогсоох:
```
Terminal 2-д: Ctrl + C
```

### PostgreSQL зогсоох:
```bash
brew services stop postgresql
```

### Redis зогсоох:
```bash
brew services stop redis
```

---

## 🔄 Дахин Эхлүүлэх (Restart)

### PostgreSQL:
```bash
brew services restart postgresql
```

### Redis:
```bash
brew services restart redis
```

### FastAPI & Celery:
```bash
# Ctrl+C дараад дахин эхлүүлэх
uvicorn src.main:app --reload --port 8000
celery -A src.infrastructure.queue.celery_app worker --loglevel=info
```

---

## 📝 Түгээмэл Асуудал & Шийдэл

### 1. "Port 8000 already in use"
```bash
# Port ашиглаж байгаа process-г олох
lsof -ti:8000

# Process-г зогсоох
kill -9 $(lsof -ti:8000)
```

### 2. "Database connection failed"
```bash
# PostgreSQL ажиллаж байгаа эсэхийг шалгах
brew services list | grep postgresql

# Эхлүүлэх
brew services start postgresql

# Database байгаа эсэхийг шалгах
psql -U postgres -l | grep study_assistant
```

### 3. "Redis connection failed"
```bash
# Redis эхлүүлэх
brew services start redis

# Шалгах
redis-cli ping
```

### 4. "Module not found"
```bash
# Virtual environment идэвхжүүлсэн эсэхийг шалгах
which python

# Хэрэв system python бол:
source venv/bin/activate

# Packages дахин суулгах
pip install -r requirements.txt
```

### 5. "Celery tasks not processing"
```bash
# Celery worker дахин эхлүүлэх
# Terminal 2-д Ctrl+C дараад:
celery -A src.infrastructure.queue.celery_app worker --loglevel=info
```

---

## 🎯 Хурдан Эхлүүлэх (Quick Start)

Хамгийн хурдан арга:

```bash
# Terminal 1
cd ~/Documents/diplom/study-assistant-backend
source venv/bin/activate
uvicorn src.main:app --reload --port 8000

# Terminal 2 (шинэ terminal)
cd ~/Documents/diplom/study-assistant-backend
source venv/bin/activate
celery -A src.infrastructure.queue.celery_app worker --loglevel=info
```

PostgreSQL болон Redis автоматаар эхэлдэг (brew services-ээр суулгасан бол).

---

## 📚 Нэмэлт Мэдээлэл

- **API Documentation**: `API_ENDPOINTS.md`
- **Postman Collection**: `AI_Study_Assistant.postman_collection.json`
- **Quick Start**: `QUICK_START.md`
- **Project Overview**: `PROJECT_COMPLETE.md`

---

## 💡 Зөвлөмж

1. **Terminal 2 ашиглах** - Нэг FastAPI, нэг Celery
2. **Logs харах** - Алдаа гарвал terminal дээр харагдана
3. **Health check хийх** - Эхлүүлсний дараа http://127.0.0.1:8000/health шалгах
4. **Auto-start тохируулах** - PostgreSQL болон Redis-г автоматаар эхлүүлэх:
   ```bash
   brew services start postgresql
   brew services start redis
   ```

---

**Амжилт хүсье! 🚀**
