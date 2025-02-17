# 使用 Python 3.9.8
FROM python:3.9.8

# 設定工作目錄
WORKDIR /app

# 複製所有檔案
COPY . .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 使用 Gunicorn 運行 Flask
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
