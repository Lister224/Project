import joblib
import pymysql
from tensorflow.keras.models import load_model
import os
from dotenv import load_dotenv
import h5py
import numpy as np

# db功能設計
class Database:
    def __init__(self, host, user, password, database, charset='utf8mb4'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.connection = None

    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset=self.charset,
                cursorclass=pymysql.cursors.DictCursor
            )

        except pymysql.MySQLError as e:
            print(f"帳密或資料庫、伺服器輸入錯誤: {e}")
            self.connection = None

    def execute_query(self, query):
        if not self.connection:
            print("沒有可用的資料庫連線")
            return None

        try:
            with self.connection.cursor() as cursor:
                if query.strip():
                    cursor.execute(query)
                    result = cursor.fetchall()
                    return result
        except pymysql.MySQLError as e:
            print(f"SQL query error: {e}")
            return None

    def close(self):
        if self.connection and self.connection.open:
            self.connection.close()


# 獲取db資料
def get_data(column_name: str):
    sql_query = f'''
        SELECT seasons, {column_name}
        FROM (
            SELECT seasons, {column_name} 
            FROM indicators
            ORDER BY seasons DESC
        ) sub
        ORDER BY seasons ASC;
    '''
    load_dotenv()
    db_host = os.environ.get('DB_HOST')
    db_user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')
    db_name = os.environ.get('DB_NAME')

    db = Database(host=db_host,
                  user=db_user,
                  password=db_password,
                  database=db_name,
                  )
    db.connect()
    result = db.execute_query(sql_query)
    db.close()
    return (result)

# 獲取指標名
def get_column_name(index_data):
    if isinstance(index_data, dict) and len(index_data) > 0:
        # 使用列表推導式來過濾 key
        keys = [key for key in index_data.keys() if key != 'seasons']
        return keys
    else:
        return []


# 輔助函數：動態獲取檔案路徑
def get_file_path(relative_path):
    base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


# 模型類型映射 (需根據實際情況調整)
MODEL_TYPE_MAPPING = {
    'ARD': 'pkl', 'ART': 'h5', 'CAPEX': 'pkl', 'CR': 'pkl',
    'CURR': 'pkl', 'DER': 'pkl', 'DR': 'pkl', 'FCFREE': 'pkl',
    'GPM': 'pkl', 'ICF': 'pkl', 'ICR': 'pkl', 'IT': 'h5',
    'ITD': 'pkl', 'LTDR': 'pkl', 'NCF': 'pkl', 'NPM': 'pkl',
    'OCD': 'pkl', 'OCF': 'h5', 'OPM': 'pkl', 'QR': 'pkl',
    'RGR_Q': 'pkl', 'ROA_Q': 'pkl', 'ROE_Q': 'pkl', 'SEQ': 'pkl',
    'TAGR_Q': 'pkl', 'TAGR_Y': 'pkl', 'TAT': 'h5'
}

# 輔助函數：自動生成未來季度
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



def predict_all_indicators(index_data):
    # 獲取指標名
    keys = get_column_name(index_data)

    # 準備返回結果的字典
    result = {"name": keys}
    for column in keys:
        result[column] = {}

        # 獲取模型類型
        model_type = MODEL_TYPE_MAPPING.get(column)
        if model_type not in ['pkl', 'h5']:
            print(f"指標 {column} 未配置模型類型或類型無效")
            continue

        # 模型路徑組合
        model_path = get_file_path(f'models/{column}_model.{model_type}')

        # 模型加載
        try:
            if model_type == 'pkl':
                model = joblib.load(model_path)
            elif model_type == 'h5':
                model = load_model(model_path)
        except FileNotFoundError:
            print(f"模型文件 {model_path} 不存在")
            continue
        except Exception as e:
            print(f"加載 {column} 模型時發生錯誤: {str(e)}")
            continue

        # 數據獲取與預處理
        raw_data = get_data(column)
        if not raw_data:
            print(f"無法取得 {column} 的數據")
            continue

        try:
            last_5_values = [item[column] for item in raw_data[-5:]]
            input_data = np.array([last_5_values]).reshape(1, -1)
            seasons = [item['seasons'] for item in raw_data][-5:]
        except KeyError:
            print(f"數據中缺少 {column} 欄位")
            continue

        # 保存原始歷史數據
        historical_values = last_5_values.copy()
        result[column]["historical"] = historical_values
        result[column]["seasons"] = seasons
        print(f"{column} 預測前數據: {historical_values}")

        # 預測過程，使用 last_5_values 的副本
        forecast_values = []
        pred_values = last_5_values.copy()  # 使用副本來進行預測
        try:
            for _ in range(3):
                input_data = np.array([pred_values]).reshape(1, -1)
                prediction = model.predict(input_data)
                prediction_value = prediction[0][0] if isinstance(prediction[0], (np.ndarray, list)) else prediction[0]

                if all(isinstance(i, int) for i in pred_values):
                    prediction_value = int(prediction_value)
                elif all(isinstance(i, float) for i in pred_values):
                    prediction_value = round(float(prediction_value), 2)

                forecast_values.append(prediction_value)

                # 更新預測數據，但不影響原始歷史數據
                pred_values.pop(0)
                pred_values.append(prediction_value)

                print(f"{column} 預測值: {prediction_value}")

        except Exception as e:
            print(f"{column} 預測失敗: {str(e)}")

        # 生成未來季度
        future_seasons = generate_future_seasons(seasons, len(forecast_values))
        result[column]["forecast"] = forecast_values
        result[column]["seasons"].extend(future_seasons)

    print('生成預測點位')
    return result



# 使用範例
if __name__ == "__main__":
    example = {'seasons': ['2024Q1', '2024Q2', '2024Q3'], 'OCF': [53.07, 53.17, 57.83]}

    # 執行預測
    if example:
        forecast_results = predict_all_indicators(example)
    print(forecast_results)