# 使用官方Python映像作為基礎映像
FROM python:3.9.8

# 設置工作目錄
WORKDIR /app

# 複製應用程序文件到工作目錄
COPY . /app

# 安裝所需的Python包
RUN pip install --no-cache-dir -r requirements.txt

# 暴露應用程式運行的端口
EXPOSE 8080

# 啟動應用程序
CMD ["python", "main.py"]

