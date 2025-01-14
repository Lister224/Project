from tensorflow.keras.layers import LSTM

class CustomLSTM(LSTM):
    def __init__(self, *args, **kwargs):
        # 移除不被支持的參數
        kwargs.pop('time_major', None)
        super().__init__(*args, **kwargs)

from tensorflow.keras.models import load_model

h5_model_path = r'C:\myclass\Project\flask_app\analysis\predict\model\lstm_capex_model.h5'

# 使用自訂 LSTM 層
model = load_model(h5_model_path, custom_objects={'LSTM': CustomLSTM})
print("模型加載成功")


