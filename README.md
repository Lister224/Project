# 📊 Finvision AI

## 📖 專案介紹
**Finvision AI** 是一款基於 **LLM（大型語言模型）** 的 AI 工具，專門用於 **財報分析**，幫助投資者與金融分析師快速解析企業財務狀況。  
此專案使用 **Python、AWS、MySQL、MongoDB、Docker** 等技術，並結合 **機器學習模型（Random Forest、LSTM）** 進行數據分析。<br>
(詳如Finvision AI簡報)

## 🚀 功能特點
- 🔍 **財務數據分析**：自動解析企業財報，提供財務指標與趨勢預測。
- 🛠 **支援多種查詢方式**：可透過 **MongoDB** 與 **MySQL** 存取財報數據。
- 📈 **數據分析與預測**：結合 **控制圖（Control Chart）、隨機森林（Random Forest）、LSTM** 進行分析。

## 🏗️ 技術架構
- **後端**：Python (Flask)
- **前端**：React / Vue / Next.js
- **資料庫**：MySQL + MongoDB Atlas
- **雲端服務**：AWS App Runner, EC2
- **容器技術**：Docker
- **數據分析**：
  - Scikit-learn（Random Forest）
  - TensorFlow（LSTM）
  - Control Chart 分析

---

## 📦 本機安裝與執行  
（如需雲端運行，請自行部署 Docker 映像檔）

### 1️⃣ **環境需求**
請確保你的環境具備以下軟體：
- Python 3.9.8
- Docker & Docker Compose
- MySQL & MongoDB Atlas
- Google Gemini 2 API 金鑰

### 2️⃣ **安裝步驟**
```bash
# 1. Clone 專案
git clone https://github.com/你的帳號/Finvision-AI.git
cd Finvision-AI

# 2. 安裝 Python 依賴
cd backend_app/
pip install -r requirements.txt

# 3. 建立 MySQL 資料庫
cd Finvision-AI/SQL_DB/
mysql -u root -p < database/finvision.sql

# 4. 申請 Google Gemini 2 API
# 請至 https://ai.google.dev/ 申請 API 金鑰，下載 JSON 檔案
# 並將其放置於 backend_app 資料夾內

# 5. 建立 .env 設定檔
編輯 .env_example，填入資料庫設定，設定後改名成.env

# 6. 修改forecast uri
修正backend_app/analysis/forecast.py 第5行，改用字的forecast_api url

# 7. 啟動後端應用程式
python backend_app/main.py
python forecast_api/app.py
```

## 🤝 貢獻者

感謝以下人員對本專案的貢獻：

- [PeiYuisme][(https://github.com/PeiYuisme)](https://github.com/PeiYuisme)
- [cys0621][(https://github.com/cys0621)](https://github.com/cys0621)
- [Eric891031][(https://github.com/Eric891031)](https://github.com/Eric891031)
- [xiang104][(https://github.com/xiang104)](https://github.com/xiang104)
- [weichen129][(https://github.com/weichen129)](https://github.com/weichen129)
