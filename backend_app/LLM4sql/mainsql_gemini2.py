from google import genai
from google.genai import types
from LLM4sql.db_utils import get_file_path, csv_read,query_database
import re
import os

credential_path = get_file_path('../gemini2.json')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

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
        return("SQL查詢指令未找到")
    
def generate_sql(user_input):
    try:
        # 讀取index欄
        csv_table = csv_read('mapping_table.csv')

        # 為不同表格預先定義欄位
        bs_columns = "seasons, TCA, TNFA, TA, TCL, TNFL, TL, TOEQ"  # 資產負債表欄位
        pl_columns = "seasons, ORV, OC, OG, OE, OI, EBT, EAT"         # 損益表欄位
        cfs_columns = "seasons, NICFO, NICFI, NICFF"          # 現金流量表欄位
        index_columns = '''seasons, GPM, OPM, NPM, ROE_Q, ROA_Q, RGR_Q, 
                        TAGR_Q, LTDR, DR, SEQ, CR, QR, CURR, ICR, ART,
                        IT, TAT, DER, ARD, ITD, OCD'''

        system_prompt = f'''
            1. 你是一個指標資料庫專家，能夠生成相應的SQL指令。 
            2. SQL的編寫請用全英文，結束請記得給分號。
            3. 非常重要!返回sql語法即可，不用其他說明與文字。
            4. MYSQL code中請不要出現資料庫中沒有的英文名稱。
            5. 請務必生成完整SQL語法，並一定要在首欄加入年或季度的欄位，例如seasons。
            6. **SQL 中報表的欄位名絕對不要使用別稱 (AS)。** 
            7. **如果使用者需要分析、查詢「所有」資料，才使用以下CODE，並自行判斷時間區間:
                SELECT {index_columns} FROM indicators order by seasons;
                SELECT {cfs_columns} FROM cfs order by seasons;
                SELECT {bs_columns} FROM bs order by seasons;
                SELECT {pl_columns} FROM pl order by seasons;。**
            8. **請務必嚴格遵守以上所有指令。**
        '''
        user_prompt = f'''
            1. **資料庫結構、表名稱、欄位名稱請務必參考以下內容:{csv_table}**
            2. **不要自己運算指標數值。若使用者需要查詢、分析某個指標，請查看{csv_table}indicators的相對應指標，不可全部查詢。**
            3. 一定不能生成沒有的sql表名與欄名，欄位名稱請盡量比對中文對照!
            4. **請務必判斷使用者輸入是否橫跨不同表，若有請1個表生出1個sql code，2個表生出2個sql code，
                3個表生出3個sql code，4個表生出3個sql code，並依照indicators第一、cfs第二、bs第三、pl第四順序生成**
            5. **若不需要用到某張表，必須生成sql SELECT * FROM 某張表 WHERE 1=0;，
                例如若不用查詢indicators，必須在第一個slq code產生SELECT * FROM indicators WHERE 1=0; 以此類推**
            6. 另外時間季度為seasons，例如2010年第一季格式為2010Q1、2010年第二季格式為2010Q2、
                2020年第三季格式為2020Q3、2020年第四季格式為2020Q4，**請幫我依照seasons由小到大排序**。
            7. **請務必嚴格遵守不要使用別稱 (AS)**
                    '''
        model= "gemini-2.0-flash-exp"
        
        generation_config = types.GenerateContentConfig(
                max_output_tokens=500,
                temperature=0.1,
                response_modalities = ["TEXT"]
                )
        
        contents = [types.Content(parts=[
                types.Part.from_text(system_prompt + user_prompt + user_input )
            ], role="user")
        ]

        response = client.models.generate_content(
                model = model,
                contents = contents,
                config = generation_config)

        sql_response = response.text
    except Exception as e:
        print(f"發生錯誤: {str(e)}，請檢查 Google Gemini API 連線狀況或稍後再試。")
        return 'LLM_error'
    
    return sql_response

# 判斷使用者問題
def classify_user_input(user_input:str):
    try:
        csv_table = csv_read('mapping_table.csv')

        model= "gemini-2.0-flash-exp"
        
        prompt = f'''
                    以下是prompt內容，請遵照。
                    1.請判斷使用者的輸入是否需要連線到「財務報表」資料庫，或是是關於「財務指標」，若需要請返回finvision即可!
                    2.**請務必讀取這個內容:{csv_table}，若使用者的輸入有在裡面，請返回finvision即可!**
                    3.若都不屬於查詢、分析財務報表或財務指標範圍，只要返回no，**不准進行聊天**!
                    4.財務報表資料庫內容包含資產負債表、損益表、現金流量表、財務指標，其餘公司資料都沒有。
                    5.問題語意不詳，例如「請、我、幫忙、我、你、他」等等，這些**只有單詞不是完整句子**，請返回no。
                    6.請務必嚴格遵守以上所有指令，你只能返回**no**或**finvision**2種狀態，一定不能返回其他任何回應。
                    '''

        content = [
                types.Content(parts=[types.Part.from_text(user_input)],role="user"),
                types.Content(parts=[types.Part.from_text(prompt)],role="user")
                ]
        
        generation_config = types.GenerateContentConfig(
                max_output_tokens=50,
                temperature=0.1,
                response_modalities = ["TEXT"]
                )    
        
        response = client.models.generate_content(
                model = model,
                contents = content,
                config = generation_config)
        print(response.text)

    except Exception as e:
        print(f"發生錯誤: {str(e)}，請檢查 Google Gemini API 連線狀況或稍後再試。")
        return 'LLM_error'
    
    return response.text
    
def llm_generate_sql(user_input):
    
    # LLM判斷使用者輸入類型
    response = classify_user_input(user_input).strip()
    
    # 系統不支援問題
    if response == 'no':
        # 返回no
        return 'no'
    
    # LLM連線異常
    if response == 'LLM_error':
        return 'LLM_error'
    
    # 生成SQL CODE
    sql_response = generate_sql(user_input)

    # LLM連線異常
    if sql_response == 'LLM_error':
        return 'LLM_error'
    
    retries = 0
    while retries <= 5:
        sql_query = extract_sql_queries(sql_response)
        if sql_query == 'SQL查詢指令未找到':
            return 'no'
        print(f'生成的SQL指令: {sql_query}')
        report = query_database(sql_query)
        if "查詢成功" in report:
            # 成功，回傳結果
            return f"finvision:{report}"
        else:
            # 失敗，再試一次
            print(f'SQL查詢失敗: {report}')
            sql_response = generate_sql(user_input + report + '若有錯誤請務必重新確認欄位與表的關係')
            retries += 1
        print(f"第{retries}次重試")
    
    # 如果達到最大重試次數，則返回錯誤訊息
    return "SQL查詢多次失敗，請稍後再試。"

if __name__ == "__main__":
    user_input ="請分析2024毛利率"
    report = llm_generate_sql(user_input)
    print(report)
    
    