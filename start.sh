#!/bin/bash
set -e

cd "$(dirname "$0")/backend"

# Create .env if not exists
if [ ! -f .env ]; then
  echo "⚠️  Chưa có file .env"
  echo "Tạo file .env từ .env.example..."
  cp .env.example .env
  echo ""
  echo "👉 Mở file backend/.env và điền ANTHROPIC_API_KEY của bạn vào"
  echo "   Sau đó chạy lại script này"
  exit 1
fi

# Install deps if needed
if ! python3 -c "import fastapi" 2>/dev/null; then
  echo "📦 Cài đặt dependencies..."
  pip3 install -r requirements.txt
fi

echo "🚀 Khởi động RAG Chatbot tại http://localhost:8000"
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
