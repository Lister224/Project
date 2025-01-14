import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import LSTM


class CustomLSTM(LSTM):
    def __init__(self, *args, **kwargs):
        # 移除不被支持的參數
        kwargs.pop('time_major', None)
        super().__init__(*args, **kwargs)

# 預測函數，返回最後 8 個點位和未來 4 個預測
def predict_with_last_points(model_path, scaled_data, future_steps, look_back, scaler):
    try:
        h5_model_path = r'C:\myclass\Project\flask_app\analysis\predict\model\lstm_capex_model.h5'

        # 使用自訂 LSTM 層
        model = load_model(h5_model_path, custom_objects={'LSTM': CustomLSTM})
        print("模型加載成功")

        # 預測用數據的最後 4 個點位
        last_8_scaled = scaled_data[-8:]
        last_8_original = scaler.inverse_transform(last_8_scaled)

        # 預測未來 4 個季度
        future_predictions = []
        last_sequence = scaled_data[-look_back:].reshape(1, look_back, 1)

        for _ in range(future_steps):
            # 使用模型進行推斷
            next_prediction = model(tf.convert_to_tensor(last_sequence, dtype=tf.float32))

            # 模型輸出是張量，直接提取數值
            future_value = next_prediction.numpy()[0, 0]
            future_predictions.append(future_value)

            # 調整 future_value 的形狀
            future_value = np.array(future_value).reshape(1, 1, 1)

            # 更新輸入序列，確保維度匹配
            last_sequence = np.append(last_sequence[:, 1:, :], future_value, axis=1)

        # 將未來預測值反歸一化
        future_predictions_original = scaler.inverse_transform(
            np.array(future_predictions).reshape(-1, 1)
        )

        return last_8_original, future_predictions_original
    except Exception as e:
        print(f"預測過程中出錯: {e}")
        return None, None


if __name__ == "__main__":
    # 設定模型路徑
    model_path = r'C:\myclass\Project\flask_app\analysis\predict\model\lstm_capex_model_saved'

    # 1. 從 CSV 文件中讀取原始數據
    file_path = r'C:\Users\TMP214\Downloads\indicators_1.csv'  # 替換為你的實際 CSV 文件路徑
    data = pd.read_csv(file_path)

    # 2. 提取所需欄位（例如 GPM）
    gpm_data = data[['CAPEX']].values

    # 3. 數據歸一化
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(gpm_data)

    # 設定參數
    look_back = 10
    future_steps = 4

    # 4. 調用預測函數
    last_8_points, future_predictions = predict_with_last_points(
        model_path, scaled_data, future_steps, look_back, scaler
    )

    # 5. 輸出結果
    if last_8_points is None or future_predictions is None:
        print("模型加載或預測失敗，請檢查日誌和輸入參數。")
    else:
        print("最後 8 個點位：")
        for i, point in enumerate(last_8_points, start=1):
            print(f"Point {i}: {point[0]:.2f}")

        print("\n未來 4 個預測：")
        for i, prediction in enumerate(future_predictions, start=1):
            print(f"Future {i}: {prediction[0]:.2f}")
