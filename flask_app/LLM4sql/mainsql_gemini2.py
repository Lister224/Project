from google import genai
from google.genai import types
from db_utils import csv_read,query_database
import base64
import re
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'D:\api\gemini2.0.json'

client = genai.Client(
        vertexai=True,
        project="gen-lang-client-0000496465",
        location="us-central1"
    )

def extract_sql_queries(sql_response):
    matches = re.findall(r'SELECT.*?;', sql_response, re.IGNORECASE | re.DOTALL) 
    if matches:
        # 移除每個匹配項中的換行符號 
        matches = [match.replace('\n', ' ') for match in matches]
        return matches 
    else: 
        raise ValueError("SQL查詢指令未找到")
    
def generate_sql_from_nl(user_input):
    csv_string = csv_read()
    system_prompt = f'''
        1. 你是一個財務資料庫專家，能夠生成相應的SQL指令。 
        2. SQL的編寫請用全英文，結束請記得給分號。
        3. 非常重要!返回sql語法即可，不用其他說明與文字。
        4. MYSQL code中請不要出現資料庫中沒有的英文名稱。
        5. 請務必生成完整SQL語法，並一定要在首欄加入年或季度的欄位，例如seasonid。
        6. **SQL 中報表的欄位名絕對不要使用別稱 (AS)。** 
        7. **若使用者需要查詢所有或整體財務資料，請回傳 SELECT * FROM cfs;SELECT * FROM bs;SELECT * FROM pl;。**
        8. **請務必嚴格遵守以上所有指令。**
       '''
    user_prompt = f'''
        1. **資料庫結構、表名稱、欄位名稱請務必參考以下內容:{csv_string}**
        2. 一定不能生成沒有的sql表名與欄名，欄位名稱請盡量比對中文對照!
        3. **請務必要判斷是否需要跨表查詢，如需要請使用join指令。**
        4. 另外時間只有年與季度seasonsID，例如2010年第一季格式為201001、2010年第二季格式為201002、
        2020年第三季格式為202003、2020年第四季格式為202004
        5. **請務必嚴格遵守不要使用別稱 (AS)**
                   '''
    model= "gemini-2.0-flash-exp"
    generation_config = types.GenerateContentConfig(
            max_output_tokens=150,
            temperature=0.1,
            response_modalities = ["TEXT"]
            )
    contents = [types.Content(parts=[
            types.Part.from_text(system_prompt + user_input + user_prompt)
        ], role="user")
    ]
    response = client.models.generate_content(
            model = model,
            contents = contents,
            config = generation_config)
    sql_response = response.text
    return sql_response

def classify_user_input(user_input:str):
    # 初次調用判斷是否需要function calling
    csv_table = csv_read('index.csv')
    model= "gemini-2.0-flash-exp"
    prompt =  f'''1.請判斷使用者的輸入是否需要連線到「財務報表」資料庫查詢，若需要請回答finvision即可!
                2.**若使用者的輸入是關於財務「指標」分析，請返回analysis即可!**
                3.**請務必讀取這個內容:{csv_table}，若使用者的輸入有在裡面，請返回analysis即可!**
                4.若都不屬於查詢、分析財務報表或財務指標範圍，只要返回no即可，不准進行聊天!
                5.財務報表資料庫內容包含資產負債表、損益表、現金流量表，其餘公司資料都沒有。
                6. **請務必嚴格遵守以上所有指令，你只能返回no或analysis或finvision三種狀態。**'''
    
    content = [types.Content(parts=[
            types.Part.from_text(prompt + user_input)
            ], role="user")
            ]
    generation_config = types.GenerateContentConfig(
        max_output_tokens=50,
        temperature=0.5,
        response_modalities = ["TEXT"]
        ) 
    response = client.models.generate_content(
            model = model,
            contents = content,
            config = generation_config)
    print('===== 初次調用LLM判斷 =====')
    if 'finvision' in response.text.lower():
        retries = 0
        sql_response = generate_sql_from_nl(user_input)
        while retries <= 5:
            sql_query = extract_sql_queries(sql_response)
            print(f'生成的SQL指令: {sql_query}')
            report = query_database(sql_query)
            if "查詢成功" in report:
                # 成功，回傳結果
                return f"finvision:{report}"
            else:
                # 失敗，再試一次
                print(f'SQL查詢失敗: {report}')
                sql_response = generate_sql_from_nl(user_input + report + '若有錯誤請務必重新確認欄位與表的關係')
                retries += 1
            print(f"第{retries}次重試")
        # 如果達到最大重試次數，則返回錯誤訊息
        return "finvision: SQL查詢多次失敗，請稍後再試。"
    else: 
        # 一般對話處理
        return(response.text)

if __name__ == "__main__":
    user_input ="請幫我查詢所有數據"
    report = classify_user_input(user_input)
    print(report)