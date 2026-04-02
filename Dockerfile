FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴檔案
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式
COPY . .

# 建立下載目錄
RUN mkdir -p downloads

# 設定環境變數
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# 暴露埠號
EXPOSE 5000

# 啟動命令
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "2"]
