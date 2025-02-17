# 📊 [Finvision AI]

## 📖 專案介紹
這個專案是 **一個用 LLM 分析財報的 AI 工具**，使用了 **Python、AWS、MySQL、MongoDB、Docker** 等技術。

## 🚀 功能特點
- 🔍 **財務數據分析**：使用 LLM 自動解析公司財報。
- 🛠 **支援多種查詢**：提供 MongoDB 和 MySQL 數據存查。

## 🏗️ 技術架構
- **後端**：Python (Flask)
- **前端**：React / Vue / Next.js
- **資料庫**：MySQL + MongoDB
- **雲端服務**：App Runner, EC2
- **容器技術**：Docker
- **數據分析**：Scikit-learn(radom forest), Tensorflow(lstm), Control chart

## 📦 安裝與執行
### 1️⃣ **環境需求**
請確保你的環境具備以下軟體：
- Python 3.9.8
- Docker & Docker Compose
- MySQL & MongoDB

### 2️⃣ **安裝步驟**
```bash
# 1. Clone 專案
git clone https://github.com/你的帳號/你的專案.git
cd 你的專案

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 啟動 Docker 容器
docker-compose up -d

# 4. 啟動應用
python app.py
