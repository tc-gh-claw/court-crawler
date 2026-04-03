#!/bin/bash
# 部署腳本 - Render

echo "🚀 開始部署到 Render..."

# Render API 設定
RENDER_API_KEY="rnd_xxxxxxxxxxxxxxxxxxxxx"  # 需要從 Render Dashboard 攞
SERVICE_NAME="court-crawler"
REPO_URL="https://github.com/tc-gh-claw/court-crawler"

# 檢查 API Key
if [ -z "$RENDER_API_KEY" ] || [ "$RENDER_API_KEY" = "rnd_xxxxxxxxxxxxxxxxxxxxx" ]; then
    echo "❌ 請先設定 RENDER_API_KEY"
    echo "去 https://dashboard.render.com/ → Account Settings → API Keys 攞"
    exit 1
fi

# 建立服務
echo "📦 建立 Render 服務..."
curl -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  https://api.render.com/v1/services \
  -d "{
    \"type\": \"web_service\",
    \"name\": \"$SERVICE_NAME\",
    \"ownerId\": \"usr-xxxxxxxx\",
    \"repo\": \"$REPO_URL\",
    \"branch\": \"main\",
    \"runtime\": \"python\",
    \"buildCommand\": \"pip install -r requirements.txt\",
    \"startCommand\": \"gunicorn app:app --bind 0.0.0.0:\$PORT\",
    \"plan\": \"free\"
  }"

echo ""
echo "✅ 部署完成！"
echo "去 https://dashboard.render.com/ 睇進度"
