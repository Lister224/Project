import pandas as pd
from google import genai
from google.genai import types
import os

def generate_financial_report(data):
    """
    基於數據生成財務報告，包括欄位解釋、趨勢分析、異常檢測和綜合評估。

    Args:
        data (list): 財務數據，為 JSON 格式的列表。

    Returns:
        str: 生成的財務報告或錯誤信息。
    """
    # 初始化客戶端
    client = genai.Client(
        vertexai=True,
        project="gen-lang-client-0000496465",
        location="us-central1"
    )

    # 設定 Google 憑證環境變數
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'D:\api\gemini2.0.json'

    # 動態獲取檔案路徑
    def get_file_path(relative_path):
        base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, relative_path)

    def csv_read_with_meanings(file_name="mapping_table.csv"):
        file_path = get_file_path(file_name)
        df = pd.read_csv(file_path, encoding='utf-8')
        required_columns = ['table_name', 'table_name_cn', 'column_name', 'column_name_cn']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"CSV 文件必須包含這些欄位: {required_columns}")
        table_meanings = {}
        for table_name, group in df.groupby('table_name'):
            table_meanings[table_name] = dict(zip(group['column_name'], group['column_name_cn']))
        return table_meanings

    def load_data_from_variable(data) -> pd.DataFrame:
        try:
            return pd.DataFrame(data)
        except Exception as e:
            raise ValueError(f"Error processing data: {e}")

    def generate_summary(data: pd.DataFrame):
        try:
            if not isinstance(data, pd.DataFrame):
                raise ValueError("輸入數據必須是 Pandas DataFrame！")
            return data.describe()
        except Exception as e:
            raise Exception(f"生成描述性統計時發生錯誤：{e}")

    def construct_prompt(user_input: str, summary_stats: pd.DataFrame) -> tuple:
        table_meanings = csv_read_with_meanings()
        system_prompt = "以下是公司內部數據欄位及意義的詳細說明：\n"
        for table_name, column_map in table_meanings.items():
            system_prompt += f"表名稱: {table_name}\n"
            for column_name, column_meaning in column_map.items():
                system_prompt += f"- {column_name}: {column_meaning}\n"
        system_prompt += (
            "\n你是一位專業數據科學家，負責從公司數據中提取洞察並撰寫報告。\n"
            "請根據以下數據進行分析並回答問題。\n"
        )
        user_prompt = (
            f"數據描述性統計如下：\n{summary_stats.to_string()}\n\n"
            f"請根據以上數據分析回答以下問題：\n{user_input}"
        )
        return system_prompt, user_prompt

    try:
        # 加載數據
        data_df = load_data_from_variable(data)
        # 生成描述性統計
        summary_stats = generate_summary(data_df)
        # 用戶查詢
        user_input = (
            "請分析財務數據並描述各季度的財務指標，包含欄位意義及異常分析。\n"
            "1欄位解釋：解釋欄位的意義。\n"
            "2趨勢分析：各指標的變化趨勢。\n"
            "3異常檢測：指出不尋常的變化並分析原因。\n"
            "4綜合評估：總結財務狀況的風險與優勢。\n"
            "不須最後的注意事項"
        )
        # 構建 GPT 模型請求的提示
        system_prompt, user_prompt = construct_prompt(user_input, summary_stats)
        # 配置模型參數
        model = "gemini-1.5-pro"
        generation_config = types.GenerateContentConfig(
            max_output_tokens=8000,
            temperature=0.1,
            response_modalities=["TEXT"]
        )
        # 構建生成內容的請求
        contents = [
            types.Content(parts=[
                types.Part.from_text(system_prompt + user_prompt)
            ], role="user")
        ]
        # 調用模型生成內容
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=generation_config
        )
        return response.text
    except Exception as e:
        return f"生成報告時發生錯誤：{e}"

# 示例調用
data = [
    {"seasons": "2022Q2", "OPM": 49.07, "QR": 195.2, "CAPEX": -217453105},
    {"seasons": "2022Q1", "OPM": 45.57, "QR": 181.7, "CAPEX": -262067090},
    {"seasons": "2021Q4", "OPM": 41.71, "QR": 187.5, "CAPEX": -235257476},
    {"seasons": "2021Q3", "OPM": 41.24, "QR": 177.4, "CAPEX": -188110486},
    {"seasons": "2021Q2", "OPM": 39.14, "QR": 162.2, "CAPEX": -166971104},
    {"seasons": "2021Q1", "OPM": 41.54, "QR": 145.7, "CAPEX": -248028725},
    {"seasons": "2020Q4", "OPM": 43.46, "QR": 151.9, "CAPEX": -88203309},
    {"seasons": "2020Q3", "OPM": 42.1, "QR": 153.9, "CAPEX": -99173345},
    {"seasons": "2020Q2", "OPM": 42.19, "QR": 123.2, "CAPEX": -126698477},
    {"seasons": "2020Q1", "OPM": 41.38, "QR": 120.1, "CAPEX": -192063846},
    {"seasons": "2023Q4", "OPM": 41.6, "QR": 206.8, "CAPEX": -143372124},
    {"seasons": "2023Q3", "OPM": 41.71, "QR": 182.9, "CAPEX": -216177778},
    {"seasons": "2023Q2", "OPM": 42.0, "QR": 207.6, "CAPEX": -241990429},
    {"seasons": "2023Q1", "OPM": 45.46, "QR": 199.0, "CAPEX": -300730596},
    {"seasons": "2022Q4", "OPM": 51.96, "QR": 189.9, "CAPEX": -330256637},
    {"seasons": "2022Q3", "OPM": 50.61, "QR": 218.0, "CAPEX": -265843866}
]

report = generate_financial_report(data)
print("生成的報告：")
print(report)
