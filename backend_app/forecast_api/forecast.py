from dotenv import load_dotenv
from tensorflow.keras.models import load_model
from multiprocessing import Pool, cpu_count
import numpy as np
import pandas as pd
import joblib
import pymysql
import os

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# 動態獲取檔案路徑
def get_file_path(relative_path):
    base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


# 預載入所有模型
MODEL_PATH = get_file_path('models')
models = {}

for filename in os.listdir(MODEL_PATH):
    if filename.endswith(".pkl"):
        model_name = filename.split("_model.pkl")[0]
        models[model_name] = joblib.load(os.path.join(MODEL_PATH, filename))
    elif filename.endswith(".h5"):
        model_name = filename.split("_model.h5")[0]
        models[model_name] = load_model(os.path.join(MODEL_PATH, filename))
print(f"✅ 預載入 {len(models)} 個模型到記憶體")

# 初始化資料庫
load_dotenv()
db_host = os.environ.get('DB_HOST')
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_name = os.environ.get('DB_NAME')


class Database:
    def __init__(self):
        self.connection = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    def execute_query(self, query):
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def close(self):
        self.connection.close()

# 從資料庫獲取最近 5 季資料（批量查詢）


def get_all_data(columns):
    column_list = ", ".join(columns)
    query = f"""
        SELECT seasons, {column_list}
        FROM indicators
        ORDER BY seasons DESC
        LIMIT 5;
    """
    db = Database()
    result = db.execute_query(query)
    db.close()
    return result[::-1]  # 反轉順序，從最舊到最新

# 取得指標名稱


def get_column_name(index_data):
    return [key for key in index_data.keys() if key != 'seasons'] if isinstance(index_data, dict) else []

# 產生未來季度名稱
def generate_future_seasons(current_seasons, num_future=3):
    last_season = current_seasons[-1]
    year, quarter = int(last_season[:4]), int(last_season[-1])

    future_seasons = []
    for _ in range(num_future):
        quarter += 1
        if quarter > 4:
            quarter = 1
            year += 1
        future_seasons.append(f"{year}Q{quarter}")
    return future_seasons



def predict_single_model(column, column_data):
    model = models.get(column)
    if model is None:
        print(f"❌ 模型 {column} 不存在")
        return column, None, None

    # ✅ 直接從 `column_data` 取得數據，而不是每次查詢 MySQL
    seasons = column_data["seasons"]
    historical_values = column_data[column]

    if not historical_values:
        print(f"❌ 指標 {column} 無法獲取數據")
        return column, None, None

    # ✅ 預測接下來的 3 季
    forecast_values = []
    pred_values = historical_values.copy()

    try:
        for _ in range(3):
            input_data = pd.DataFrame([pred_values])
            prediction = model.predict(input_data)
            prediction_value = prediction[0] if isinstance(
                prediction, np.ndarray) else prediction

            if isinstance(prediction_value, np.ndarray) and prediction_value.ndim > 0:
                prediction_value = prediction_value.item()

            prediction_value = int(prediction_value) if all(isinstance(
                i, int) for i in pred_values) else round(float(prediction_value), 2)

            forecast_values.append(prediction_value)
            pred_values.pop(0)
            pred_values.append(prediction_value)

    except Exception as e:
        print(f"❌ {column} 預測失敗: {e}")

    # ✅ 生成未來季度
    future_seasons = generate_future_seasons(seasons, len(forecast_values))

    return column, historical_values + forecast_values, seasons + future_seasons

# ✅ 修正：使用 `starmap()` 避免 `pickle` 問題
def predict_all_indicators(index_data):
    keys = get_column_name(index_data)

    # ✅ 一次查詢所有指標數據
    raw_data = get_all_data(keys)
    df = pd.DataFrame(raw_data)

    # ✅ 確保 df 內所有指標都有數據
    df.columns = ['seasons'] + keys

    # ✅ 將數據轉為字典
    indicator_data = {col: df[['seasons', col]].dropna().to_dict(orient='list') for col in keys}

    results = []
    for col in keys:
        result = predict_single_model(col, indicator_data[col])
        results.append(result)

    # ✅ 整理結果
    temp_result = {}
    for column, values, season_list in results:
        if values and season_list:
            temp_result[column] = {
                "historical": values[:-3],
                "forecast": values[-3:],
                "seasons": season_list
            }

    # ✅ 轉換為最終格式
    final_result = {"name": list(temp_result.keys())}  # 先加上 "name" 欄位
    final_result.update(temp_result)  # 加上指標數據

    return final_result



# 測試案例
if __name__ == "__main__":
    example = {
        'seasons': ['2024Q1', '2024Q2', '2024Q3'],
        'OCF': [], 'ARD': []
    }

    # 執行預測
    if example:
        forecast_results = predict_all_indicators(example)
    print(forecast_results)
