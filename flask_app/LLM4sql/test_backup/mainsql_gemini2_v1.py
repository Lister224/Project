from google import genai
from google.genai import types
from ..db_utils import csv_read,query_database
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
    
def generate_finvision_sql(user_input):

    # 讀取finvison欄
    csv_string = csv_read('finvision_tables_and_columns.csv')

    # 為不同表格預先定義欄位
    bs_columns = "seasons, TCA, TNFA, TA, TCL, TNFL, TL, TOEQ"  # 資產負債表欄位
    pl_columns = "seasons, ORV, OC, OG, OE, OI, EBT, EAT"         # 損益表欄位
    cfs_columns = "seasons, NICFO, NICFI, NICFF"          # 現金流量表欄位

    system_prompt = f'''
        1. 你是一個財務資料庫專家，能夠生成相應的SQL指令。 
        2. SQL的編寫請用全英文，結束請記得給分號。
        3. 非常重要!返回sql語法即可，不用其他說明與文字。
        4. MYSQL code中請不要出現資料庫中沒有的英文名稱。
        5. 請務必生成完整SQL語法，並一定要在首欄加入年或季度的欄位，例如seasons。
        6. **SQL 中報表的欄位名絕對不要使用別稱 (AS)。** 
        7. **若使用者需要查詢所有或整體財務報表資料，請使用以下CODE，並自行判斷時間區間:
            SELECT {cfs_columns} FROM cfs order by seasons;
            SELECT {bs_columns} FROM bs order by seasons;
            SELECT {pl_columns} FROM pl order by seasons;。**
            SELECT {pl_columns} FROM pl order by seasons;。**
        8. **請務必嚴格遵守以上所有指令。**
       '''
    user_prompt = f'''
        1. **資料庫結構、表名稱、欄位名稱請務必參考以下內容:{csv_string}**
        2. 一定不能生成沒有的sql表名與欄名，欄位名稱請盡量比對中文對照!
        3. **請務必判斷使用者輸入是否橫跨不同表，若有請1個表生出1個sql code，2個表生出2個sql code，
             3個表生出3個sql code，並依照cfs第一、bs第二、pl第三順序生成**
        4. **若不需要用到某張表，必須生成sql SELECT * FROM 某張表 WHERE 1=0;，
            例如若不用查詢cfs，必須在第一個slq code產生SELECT * FROM cfs WHERE 1=0; 以此類推**
        5. 另外時間只季度seasons，例如2010年第一季格式為2010Q1、2010年第二季格式為2010Q2、
            2020年第三季格式為2020Q3、2020年第四季格式為2020Q4，**請幫我依照seasons由小到大排序**。
        6. **請務必嚴格遵守不要使用別稱 (AS)**
                   '''
    model= "gemini-2.0-flash-exp"
    
    generation_config = types.GenerateContentConfig(
            max_output_tokens=500,
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



def generate_index_sql(user_input):
    
    # 讀取index欄
    csv_string = csv_read('index.csv')

    # 為不同表格預先定義欄位
    bs_columns = "seasons, TCA, TNFA, TA, TCL, TNFL, TL, TOEQ"  # 資產負債表欄位
    pl_columns = "seasons, ORV, OC, OG, OE, OI, EBT, EAT"         # 損益表欄位
    cfs_columns = "seasons, NICFO, NICFI, NICFF"          # 現金流量表欄位
    index_columns = '''seasons, GPM, OPM, NPM, ROE-Q, ROA-Q, RGR-Q, 
                        TAGR-Q, LTDR, DR, SEQ, CR, QR, CURR, ICR, ART,
                        IT, TAT, DER, ARD, ITD, OCD, OCF, ICF, FCF,
                        CAPEX, FCFREE, NCF'''

    system_prompt = f'''
        1. 你是一個指標資料庫專家，能夠生成相應的SQL指令。 
        2. SQL的編寫請用全英文，結束請記得給分號。
        3. 非常重要!返回sql語法即可，不用其他說明與文字。
        4. MYSQL code中請不要出現資料庫中沒有的英文名稱。
        5. 請務必生成完整SQL語法，並一定要在首欄加入年或季度的欄位，例如seasons。
        6. **SQL 中報表的欄位名絕對不要使用別稱 (AS)。** 
        7. **若使用者需要分析所有或整體資料，請使用以下CODE，並自行判斷時間區間:
            SELECT {index_columns} FROM indicators order by seasons;
            SELECT {cfs_columns} FROM cfs order by seasons;
            SELECT {bs_columns} FROM bs order by seasons;
            SELECT {pl_columns} FROM pl order by seasons;。**
        8. **請務必嚴格遵守以上所有指令。**
       '''
    user_prompt = f'''
        1. **欄位名稱請務必參考以下內容:{csv_string}**
        2. 一定不能生成沒有的sql表名與欄名，欄位名稱請盡量比對中文對照!
        3. 另外時間只季度seasons，例如2010年第一季格式為2010Q1、2010年第二季格式為2010Q2、
        2020年第三季格式為2020Q3、2020年第四季格式為2020Q4，**請幫我依照seasons由小到大排序**。
        4. **請務必嚴格遵守不要使用別稱 (AS)**
                   '''
    model= "gemini-2.0-flash-exp"
    
    generation_config = types.GenerateContentConfig(
            max_output_tokens=500,
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
    
    prompt = f'''1.請判斷使用者的輸入是否需要連線到「財務報表」資料庫查詢，若需要請回答finvision即可!
                2.若使用者的輸入是關於「財務指標」或分析，請返回analysis即可!
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
    print(response.text)
    return response.text
    
    
def llm_generate_sql(user_input):
    # LLM判斷使用者輸入類型
    response = classify_user_input(user_input)

    print('===== 初次調用LLM判斷 =====')
    if 'finvision' in response.lower():
        retries = 0
        sql_response = generate_finvision_sql(user_input)
        print(sql_response)
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
                sql_response = generate_finvision_sql(user_input + report + '若有錯誤請務必重新確認欄位與表的關係')
                retries += 1
            print(f"第{retries}次重試")
        
        # 如果達到最大重試次數，則返回錯誤訊息
        return "SQL查詢多次失敗，請稍後再試。"
    
    elif 'analysis' in response.lower():
        retries = 0
        sql_response = generate_index_sql(user_input)
        print(sql_response)
        while retries <= 5:
            sql_query = extract_sql_queries(sql_response)
            print(f'生成的SQL指令: {sql_query}')
            report = query_database(sql_query)
            if "查詢成功" in report:
                # 成功，回傳結果
                return f"analysis:{report}"
            else:
                # 失敗，再試一次
                print(f'SQL查詢失敗: {report}')
                sql_response = generate_index_sql(user_input + report + '若有錯誤請務必重新確認欄位名稱')
                retries += 1
            print(f"第{retries}次重試")
            
        # 如果達到最大重試次數，則返回錯誤訊息
        return "SQL查詢多次失敗，請稍後再試。"

    else:
        # 返回no
        return f"no"

if __name__ == '__main__':
    user_input ="請給我2023年各季度之利息收入、銷貨收入"
    report = llm_generate_sql(user_input)
    print(report)
