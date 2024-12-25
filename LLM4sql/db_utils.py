import pymysql 
import pandas as pd 
from json import loads, dumps 
import json
from datetime import datetime,date
from decimal import Decimal

# 連接到資料庫
def connect_to_db():
    try:
        connection = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='xxxxxxxx',
            database='finvison',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("連線成功")
        return connection
    except pymysql.MySQLError as e:
        print(f"帳密或資料庫、伺服器輸入錯誤: {e}")
        return None

# 執行多筆SQL查詢
def execute_sql(connection, queries): 
    try: 
        with connection.cursor() as cursor: 
            results = [] 
            # 拆分成多個 SQL 語句 
            for query in queries:
                if query.strip(): # 確保語句不為空 
                    cursor.execute(query) 
                    results.append(cursor.fetchall()) 
            return results 
    except pymysql.MySQLError as e: 
        return f"SQL query error: {e}" 
    finally: connection.close()

# datetime格式轉換
def default_converter(o):
    if isinstance(o, (datetime,date)):
        return o.isoformat()
    elif isinstance(o, Decimal):  # 如果還有其他類型，例如date
        return float(o)
    else:
        raise TypeError(f'Object of type {o.__class__.__name__} is not JSON serializable')

# 返回查詢結果，轉json
def query_database(sql_query: str):
    connection = connect_to_db()
    if connection:
        result = execute_sql(connection, sql_query)
        return json.dumps(result, default=default_converter, ensure_ascii=False)
    else:
        return "無法連接到資料庫"
    
# 讀取csv print csv
def csv_read(file_path='finvison_tables_and_columns.csv'):
    df = pd.read_csv(file_path)
    csv_string = df.to_csv(index=False)
    return csv_string

# # 測試連線
# sql_query =  ['SELECT NSR FROM pl WHERE seasonsID = 202001;']
# result = query_database(sql_query)
# print(result)


#     # 建立映射表
# def load_mapping_from_csv(file_path='tables_and_columns.csv'):
#     df = pd.read_csv(file_path,encoding='utf-8')
#     result = df.to_json(orient="records",force_ascii=False)
#     parsed = loads(result)
#     return dumps(parsed, indent=4,ensure_ascii=False)  

# # 模糊比對找最佳匹配(成果不理想，遺棄)
# def find_best_match(user_input, mapping_table,thresold=30): 
#     matches = []
#     # 比對表名 
#     for english_table_name, names in mapping_table.items(): 
#         score = fuzz.ratio(user_input, names['chinese_table_name']) 
#         if score > thresold: 
#             matches.append({
#             'table_name': english_table_name, 
#             'column_name': None, 
#             'score': score
#             })

#         # 比對欄位名 
#         for english_column_name, chinese_column_name in names['columns'].items():
#             score = fuzz.ratio(user_input, chinese_column_name) 
#             if score > thresold: 
#                 matches.append({
#                         'table_name': english_table_name, 
#                         'column_name':english_column_name, 
#                         'score': score
#                     })
                
#     # 根據分數排序，返回匹配結果 
#     matches = sorted(matches, key=lambda x: x['score'], reverse=True)
#     return matches
