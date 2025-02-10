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

# 動態獲取檔案路徑
def get_file_path(relative_path):
    base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# 設定 Google 憑證環境變數
credential_path = get_file_path('../gemini2.json')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

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
        if not data:  # 檢查是否為空列表
            raise ValueError("Empty data list")
        return pd.DataFrame(data)
    except Exception as e:
        raise ValueError(f"Error processing data: {e}")

# 確認是否pandas格式、生成描述統計報告
def generate_summary(data: pd.DataFrame):
    try:
        if not isinstance(data, pd.DataFrame):
            raise ValueError("輸入數據必須是 Pandas DataFrame！")
        print('生成描述性統計')
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
        dfs = [load_data_from_variable(data) for data in data_list if data]
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
            "不須呈現報告日期、報告目的、數據來源、分析方法、開頭回復，只要**單純呈現報告內容**即可。\n"
            "一定不要在報告中生成表格，只要文字報告即可。\n"
           )
        
        # 構建 GPT 模型請求的提示
        system_prompt, user_prompt = construct_prompt(user_input, summary_stats,combined_data)
        
        # 配置模型參數
        model = "gemini-2.0-flash-exp"
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
        print('生成報告')
        return response.text
    except Exception as e:
        return f"生成報告時發生錯誤：{e}"

if __name__ == '__main__':
    # 示例調用
    data = [[{"seasons": "2022Q1", "GPM": 55.63, "OPM": 45.57, "NPM": 41.31, "ROE_Q": 9.03, "ROA_Q": 5.26, "RGR_Q": 12.07, "TAGR_Q": 7.17, "LTDR": 15.85, "DR": 41.86, "SEQ": 58.14, "CR": 139.9, "QR": 181.7, "CURR": 209.3, "ICR": 107.0, "ART": 9.54, "IT": 4.43, "TAT": 0.51, "DER": 71.99, "ARD": 37.66, "ITD": 81.08, "OCD": 118.74, "OCF": 372169688, "ICF": -288073791, "FCF": -19086188, "CAPEX": -262067090, "FCFREE": 110102598, "NCF": 65009709}, {"seasons": "2022Q2", "GPM": 59.06, "OPM": 49.07, "NPM": 44.4, "ROE_Q": 9.82, "ROA_Q": 5.69, "RGR_Q": 8.77, "TAGR_Q": 8.85, "LTDR": 17.42, "DR": 42.23, "SEQ": 57.77, "CR": 148.3, "QR": 195.2, "CURR": 225.5, "ICR": 92.59, "ART": 9.75, "IT": 4.19, "TAT": 0.51, "DER": 73.11, "ARD": 36.73, "ITD": 85.71, "OCD": 122.44, "OCF": 338849429, "ICF": -275932106, "FCF": 19080454, "CAPEX": -217453105, "FCFREE": 121396324, "NCF": 81997777}, {"seasons": "2022Q3", "GPM": 60.43, "OPM": 50.61, "NPM": 45.82, "ROE_Q": 10.68, "ROA_Q": 6.25, "RGR_Q": 14.79, "TAGR_Q": 6.84, "LTDR": 18.21, "DR": 40.73, "SEQ": 59.27, "CR": 160.5, "QR": 218.0, "CURR": 249.5, "ICR": 94.97, "ART": 10.09, "IT": 4.45, "TAT": 0.55, "DER": 68.71, "ARD": 35.43, "ITD": 81.08, "OCD": 116.51, "OCF": 412698167, "ICF": -284390325, "FCF": -130406753, "CAPEX": -265843866, "FCFREE": 146854301, "NCF": -2098911}, {"seasons": "2022Q4", "GPM": 62.22, "OPM": 51.96, "NPM": 47.3, "ROE_Q": 10.36, "ROA_Q": 6.16, "RGR_Q": 2.02, "TAGR_Q": 6.92, "LTDR": 16.9, "DR": 40.37, "SEQ": 59.63, "CR": 142.2, "QR": 189.9, "CURR": 217.4, "ICR": 101.4, "ART": 10.15, "IT": 4.3, "TAT": 0.52, "DER": 67.7, "ARD": 35.43, "ITD": 83.33, "OCD": 118.76, "OCF": 486881904, "ICF": -342532013, "FCF": -69831545, "CAPEX": -330256637, "FCFREE": 156625267, "NCF": 74518346}, {"seasons": "2023Q1", "GPM": 56.33, "OPM": 45.46, "NPM": 40.69, "ROE_Q": 6.84, "ROA_Q": 4.13, "RGR_Q": -18.69, "TAGR_Q": 1.63, "LTDR": 16.94, "DR": 38.7, "SEQ": 61.3, "CR": 158.7, "QR": 199.0, "CURR": 228.6, "ICR": 83.42, "ART": 10.72, "IT": 4.06, "TAT": 0.41, "DER": 63.14, "ARD": 33.58, "ITD": 88.24, "OCD": 121.82, "OCF": 385244745, "ICF": -272231795, "FCF": -64487030, "CAPEX": -300730596, "FCFREE": 84514149, "NCF": 48525920}, {"seasons": "2023Q2", "GPM": 54.11, "OPM": 42.0, "NPM": 37.79, "ROE_Q": 5.77, "ROA_Q": 3.56, "RGR_Q": -5.46, "TAGR_Q": 2.05, "LTDR": 17.62, "DR": 37.75, "SEQ": 62.25, "CR": 157.5, "QR": 207.6, "CURR": 241.7, "ICR": 72.44, "ART": 11.26, "IT": 3.92, "TAT": 0.38, "DER": 60.65, "ARD": 31.69, "ITD": 91.84, "OCD": 123.53, "OCF": 167247979, "ICF": -259326076, "FCF": -26588885, "CAPEX": -241990429, "FCFREE": -74742450, "NCF": -118666982}, {"seasons": "2023Q3", "GPM": 54.26, "OPM": 41.71, "NPM": 38.56, "ROE_Q": 6.41, "ROA_Q": 3.96, "RGR_Q": 13.7, "TAGR_Q": 6.51, "LTDR": 17.09, "DR": 38.5, "SEQ": 61.5, "CR": 135.2, "QR": 182.9, "CURR": 214.7, "ICR": 78.75, "ART": 10.5, "IT": 4.03, "TAT": 0.41, "DER": 62.61, "ARD": 34.09, "ITD": 89.11, "OCD": 123.2, "OCF": 294645276, "ICF": -242243223, "FCF": -38451204, "CAPEX": -216177778, "FCFREE": 78467498, "NCF": 13950849}, {"seasons": "2023Q4", "GPM": 53.04, "OPM": 41.6, "NPM": 38.1, "ROE_Q": 6.95, "ROA_Q": 4.33, "RGR_Q": 14.41, "TAGR_Q": 0.87, "LTDR": 16.6, "DR": 37.04, "SEQ": 62.96, "CR": 160.4, "QR": 206.8, "CURR": 240.2, "ICR": 96.35, "ART": 11.78, "IT": 4.58, "TAT": 0.45, "DER": 58.83, "ARD": 30.51, "ITD": 78.26, "OCD": 108.77, "OCF": 394829347, "ICF": -132319502, "FCF": -75367133, "CAPEX": -143372124, "FCFREE": 251457223, "NCF": 187142712}, {"seasons": "2024Q1", "GPM": 53.07, "OPM": 42.02, "NPM": 38.0, "ROE_Q": 6.3, "ROA_Q": 3.98, "RGR_Q": -5.26, "TAGR_Q": 4.62, "LTDR": 16.68, "DR": 36.67, "SEQ": 63.33, "CR": 165.5, "QR": 207.1, "CURR": 239.0, "ICR": 99.78, "ART": 11.73, "IT": 4.29, "TAT": 0.42, "DER": 57.89, "ARD": 30.72, "ITD": 84.11, "OCD": 114.83, "OCF": 436311108, "ICF": -159806991, "FCF": -71685617, "CAPEX": -181121318, "FCFREE": 255189790, "NCF": 204818500}, {"seasons": "2024Q2", "GPM": 53.17, "OPM": 42.55, "NPM": 36.77, "ROE_Q": 6.62, "ROA_Q": 4.21, "RGR_Q": 13.64, "TAGR_Q": 3.36, "LTDR": 16.29, "DR": 36.14, "SEQ": 63.86, "CR": 171.5, "QR": 215.6, "CURR": 247.1, "ICR": 117.1, "ART": 12.99, "IT": 4.68, "TAT": 0.46, "DER": 56.6, "ARD": 27.52, "ITD": 76.92, "OCD": 104.44, "OCF": 377668210, "ICF": -197607330, "FCF": -90244583, "CAPEX": -197901488, "FCFREE": 179766722, "NCF": 89816297}, {"seasons": "2024Q3", "GPM": 57.83, "OPM": 47.49, "NPM": 42.79, "ROE_Q": 8.29, "ROA_Q": 5.35, "RGR_Q": 12.8, "TAGR_Q": 3.06, "LTDR": 15.18, "DR": 34.77, "SEQ": 65.23, "CR": 174.6, "QR": 223.8, "CURR": 256.7, "ICR": 146.8, "ART": 13.14, "IT": 4.53, "TAT": 0.5, "DER": 53.3, "ARD": 27.27, "ITD": 79.65, "OCD": 106.92, "OCF": 391992467, "ICF": -195509921, "FCF": -83638287, "CAPEX": -198992229, "FCFREE": 193000238, "NCF": 112844259}], [], [], [{"seasons": "2022Q1", "ORV": 491100000, "OC": 217900000, "OG": 273200000, "OE": 48610000, "OI": 223800000, "EBT": 226800000, "EAT": 202700000}, {"seasons": "2022Q2", "ORV": 534100000, "OC": 218700000, "OG": 315500000, "OE": 53370000, "OI": 262100000, "EBT": 266000000, "EAT": 237000000}, {"seasons": "2022Q3", "ORV": 613100000, "OC": 242600000, "OG": 370500000, "OE": 60190000, "OI": 310300000, "EBT": 316700000, "EAT": 280900000}, {"seasons": "2022Q4", "ORV": 625500000, "OC": 236300000, "OG": 389200000, "OE": 64540000, "OI": 325000000, "EBT": 334700000, "EAT": 295900000}, {"seasons": "2023Q1", "ORV": 508600000, "OC": 222100000, "OG": 286500000, "OE": 55310000, "OI": 231200000, "EBT": 244300000, "EAT": 207000000}, {"seasons": "2023Q2", "ORV": 480800000, "OC": 220600000, "OG": 260200000, "OE": 58190000, "OI": 202000000, "EBT": 214700000, "EAT": 181800000}, {"seasons": "2023Q3", "ORV": 546700000, "OC": 250100000, "OG": 296600000, "OE": 68710000, "OI": 228100000, "EBT": 241900000, "EAT": 211000000}, {"seasons": "2023Q4", "ORV": 625500000, "OC": 293800000, "OG": 331800000, "OE": 71620000, "OI": 260200000, "EBT": 278300000, "EAT": 238700000}, {"seasons": "2024Q1", "ORV": 592600000, "OC": 278100000, "OG": 314500000, "OE": 65360000, "OI": 249000000, "EBT": 266500000, "EAT": 225500000}, {"seasons": "2024Q2", "ORV": 673500000, "OC": 315400000, "OG": 358100000, "OE": 70300000, "OI": 286600000, "EBT": 306300000, "EAT": 247800000}, {"seasons": "2024Q3", "ORV": 759700000, "OC": 320300000, "OG": 439300000, "OE": 79080000, "OI": 360800000, "EBT": 384200000, "EAT": 325300000}]]
    report = generate_report(data)
    print("生成的報告：")
    print(report)
