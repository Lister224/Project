import requests

# 指標預測存取
def predict_all_indicators(indicator):
    url = "http://54.160.198.72/predict" # 這裡請改用你的forecast 網址

    try:
        response = requests.post(url, json= indicator)
        response.raise_for_status()  # 檢查 HTTP 錯誤

        result = response.json()

        # 將 name 提前並只返回 predictions 值
        filtered_result = {
            'name': result.get("predictions", {}).get('name'),
            **{key: value for key, value in result.get("predictions", {}).items() if key != 'name'}
        }
        print('預測結果生成')
        return filtered_result
    except requests.exceptions.RequestException as e:
        print(f"API 請求錯誤: {e}")
        return 'error'

if __name__ == "__main__":
    indicator= {
        "seasons": ["2024Q1", "2024Q2", "2024Q3"],
        "OCF": [], "ARD": []
    }
    results = predict_all_indicators(indicator)
    print(f"結果：{results}")
