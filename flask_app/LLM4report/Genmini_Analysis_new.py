import pandas as pd
from google import genai
from google.genai import types
import os

# 初始化客戶端
client = genai.Client(
    vertexai=True,
    project="gen-lang-client-0000496465",
    location="us-central1"
)

# 設定 Google 憑證環境變數
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"D:\api\gemini2.0.json"

# 動態獲取檔案路徑
def get_file_path(relative_path):
    base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# 讀取映射表
def csv_read_with_meanings(file_name="mapping_table.csv"):
    file_path = get_file_path(file_name)
    df = pd.read_csv(file_path, encoding='utf-8')
    required_columns = ['table_name', 'table_name_cn', 'column_name', 'column_name_cn']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"CSV 文件必須包含這些欄位: {required_columns}")
    column_meanings = dict(zip(df['column_name'], df['column_name_cn']))
    return column_meanings

# data轉pandas格式
def load_data_from_variable(data) -> pd.DataFrame:
    try:
        return pd.DataFrame(data)
    except Exception as e:
        raise ValueError(f"Error processing data: {e}")

# 確認是否pandas格式、生成描述統計報告
def generate_summary(data: pd.DataFrame):
    try:
        if not isinstance(data, pd.DataFrame):
            raise ValueError("輸入數據必須是 Pandas DataFrame！")
        return data.describe()
    except Exception as e:
        raise Exception(f"生成描述性統計時發生錯誤：{e}")

# prompt設定
def construct_prompt(user_input: str, summary_stats: pd.DataFrame,data: pd.DataFrame) -> tuple:
    system_prompt = f'''
        1.你是一位專業數據科學家以及財務專家，負責從公司數據中提取洞察並撰寫繁體中文報告。
        2.請了解所有數據資料，資料如下:{data}。
        3.請根據數據進行分析並回答問題。
    '''
    user_prompt = (
        f"數據描述性統計如下：\n{summary_stats.to_string()}\n\n"
        f"請根據提供資訊回答問題：\n{user_input}"
    )
    return system_prompt, user_prompt

# 主要生成報告
def generate_report(data_list):
    """
    基於多組數據生成綜合財務報告，包括欄位解釋、趨勢分析、異常檢測和綜合評估。

    Args:
        data_list (list): 包含多組數據的列表，每組數據為 JSON 格式的列表。

    Returns:
        str: 生成的綜合財務報告或錯誤信息。
    """
    try:
        # 將多組數據合併到同一個 DataFrame 中
        dfs = [load_data_from_variable(data) for data in data_list]
        combined_data = dfs[0]
        for df in dfs[1:]:
            combined_data = pd.merge(combined_data, df, on='seasons', how='outer')
        
        # 讀取映射表，將欄位名稱轉換成中文名稱
        column_meanings = csv_read_with_meanings()
        combined_data.rename(columns=column_meanings, inplace=True)
        print(combined_data)
        
        # 生成描述性統計
        summary_stats = generate_summary(combined_data)
        print(summary_stats)
        
        # 用戶查詢
        user_input = (
            "請分析財務數據並描述各季度的財務指標及財報數據，最好能提出具體數字，越詳盡越好。\n"
            "1趨勢分析：各指標的變化趨勢。\n"
            "2異常檢測：指出不尋常的變化並分析原因。\n"
            "3綜合評估：總結財務狀況的風險與優勢。\n"
            "不須呈現報告日期、報告目的、數據來源、分析方法"
        )
        
        # 構建 GPT 模型請求的提示
        system_prompt, user_prompt = construct_prompt(user_input, summary_stats,combined_data)
        
        # 配置模型參數
        model = "gemini-2.0-flash-thinking-exp-1219"
        generation_config = types.GenerateContentConfig(
            max_output_tokens=8000,
            temperature= 0.8,
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

if __name__ == '__main__':
    # 示例調用
    data = [[{"seasons": "2022Q1", "NICFO": 372200000, "NICFI": -288100000, "NICFF": -19090000}, {"seasons": "2022Q2", "NICFO": 338800000, "NICFI": -275900000, "NICFF": 19080000}, {"seasons": "2022Q3", "NICFO": 412700000, "NICFI": -284400000, "NICFF": -130400000}, {"seasons": "2022Q4", "NICFO": 486900000, "NICFI": -342500000, "NICFF": -69830000}, {"seasons": "2023Q1", "NICFO": 385200000, "NICFI": -272200000, "NICFF": -64490000}, {"seasons": "2023Q2", "NICFO": 167200000, "NICFI": -259300000, "NICFF": -26590000}, {"seasons": "2023Q3", "NICFO": 294600000, "NICFI": -242200000, "NICFF": -38450000}, {"seasons": "2023Q4", "NICFO": 394800000, "NICFI": -132300000, "NICFF": -75370000}, {"seasons": "2024Q1", "NICFO": 436300000, "NICFI": -159800000, "NICFF": -71690000}, {"seasons": "2024Q2", "NICFO": 377700000, "NICFI": -197600000, "NICFF": -90240000}, {"seasons": "2024Q3", "NICFO": 392000000, "NICFI": -195500000, "NICFF": -83640000}], [{"seasons": "2022Q1", "TCA": 1722237632, "TNFA": 2270439035, "TA": 3992676667, "TCL": 822867707, "TNFL": 848340206, "TL": 1671207913, "TOEQ": 2321468754}, {"seasons": "2022Q2", "TCA": 1905866396, "TNFA": 2440074939, "TA": 4345941335, "TCL": 845240981, "TNFL": 990238229, "TL": 1835479210, "TOEQ": 2510462125}, {"seasons": "2022Q3", "TCA": 2014232358, "TNFA": 2629069408, "TA": 4643301766, "TCL": 807431287, "TNFL": 1083554320, "TL": 1890985607, "TOEQ": 2752316159}, {"seasons": "2022Q4", "TCA": 2052896744, "TNFA": 2911882134, "TA": 4964778878, "TCL": 944226817, "TNFL": 1060063194, "TL": 2004290011, "TOEQ": 2960488867}, {"seasons": "2023Q1", "TCA": 1995727521, "TNFA": 3050116827, "TA": 5045844348, "TCL": 873089921, "TNFL": 1079856829, "TL": 1952946750, "TOEQ": 3092897598}, {"seasons": "2023Q2", "TCA": 1959964207, "TNFA": 3189500838, "TA": 5149465045, "TCL": 810829007, "TNFL": 1133167839, "TL": 1943996846, "TOEQ": 3205468199}, {"seasons": "2023Q3", "TCA": 2082477636, "TNFA": 3402078745, "TA": 5484556381, "TCL": 970034816, "TNFL": 1141703458, "TL": 2111738274, "TOEQ": 3372818107}, {"seasons": "2023Q4", "TCA": 2194032910, "TNFA": 3338338305, "TA": 5532371215, "TCL": 913583316, "TNFL": 1135525052, "TL": 2049108368, "TOEQ": 3483262847}, {"seasons": "2024Q1", "TCA": 2452767394, "TNFA": 3335123688, "TA": 5787891082, "TCL": 1026180079, "TNFL": 1095994749, "TL": 2122174828, "TOEQ": 3665716254}, {"seasons": "2024Q2", "TCA": 2591658093, "TNFA": 3390705921, "TA": 5982364014, "TCL": 1048915680, "TNFL": 1113300129, "TL": 2162215809, "TOEQ": 3820148205}, {"seasons": "2024Q3", "TCA": 2773913863, "TNFA": 3391744313, "TA": 6165658176, "TCL": 1080399099, "TNFL": 1063336786, "TL": 2143735885, "TOEQ": 4021922291}], [{"seasons": "2022Q1", "ORV": 491100000, "OC": 217900000, "OG": 273200000, "OE": 48610000, "OI": 223800000, "EBT": 226800000, "EAT": 202700000}, {"seasons": "2022Q2", "ORV": 534100000, "OC": 218700000, "OG": 315500000, "OE": 53370000, "OI": 262100000, "EBT": 266000000, "EAT": 237000000}, {"seasons": "2022Q3", "ORV": 613100000, "OC": 242600000, "OG": 370500000, "OE": 60190000, "OI": 310300000, "EBT": 316700000, "EAT": 280900000}, {"seasons": "2022Q4", "ORV": 625500000, "OC": 236300000, "OG": 389200000, "OE": 64540000, "OI": 325000000, "EBT": 334700000, "EAT": 295900000}, {"seasons": "2023Q1", "ORV": 508600000, "OC": 222100000, "OG": 286500000, "OE": 55310000, "OI": 231200000, "EBT": 244300000, "EAT": 207000000}, {"seasons": "2023Q2", "ORV": 480800000, "OC": 220600000, "OG": 260200000, "OE": 58190000, "OI": 202000000, "EBT": 214700000, "EAT": 181800000}, {"seasons": "2023Q3", "ORV": 546700000, "OC": 250100000, "OG": 296600000, "OE": 68710000, "OI": 228100000, "EBT": 241900000, "EAT": 211000000}, {"seasons": "2023Q4", "ORV": 625500000, "OC": 293800000, "OG": 331800000, "OE": 71620000, "OI": 260200000, "EBT": 278300000, "EAT": 238700000}, {"seasons": "2024Q1", "ORV": 592600000, "OC": 278100000, "OG": 314500000, "OE": 65360000, "OI": 249000000, "EBT": 266500000, "EAT": 225500000}, {"seasons": "2024Q2", "ORV": 673500000, "OC": 315400000, "OG": 358100000, "OE": 70300000, "OI": 286600000, "EBT": 306300000, "EAT": 247800000}, {"seasons": "2024Q3", "ORV": 759700000, "OC": 320300000, "OG": 439300000, "OE": 79080000, "OI": 360800000, "EBT": 384200000, "EAT": 325300000}]]
    report = generate_report(data)
    print("生成的報告：")
    print(report)
