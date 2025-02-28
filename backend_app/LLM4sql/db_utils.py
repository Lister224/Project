import os
import pymysql 
import pandas as pd 
import json
from dotenv import load_dotenv
from datetime import datetime,date
from decimal import Decimal

# db功能設計
class Database:
    def __init__(self, host, user, password, database, charset='utf8mb4'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.connection = None

    # 連接到資料庫
    def connect(self):
        try:
            self.connection = pymysql.connect(
                host= self.host,
                user= self.user,
                password= self.password,
                database= self.database,
                charset= self.charset,
                cursorclass=pymysql.cursors.DictCursor
            )
            print("連線成功")
            return self.connection
        
        except pymysql.MySQLError as e:
            print(f"帳密或資料庫、伺服器輸入錯誤: {e}")
            return None
        
    # 資料庫查詢結果結構重構
    @staticmethod
    def restructure_data(results):
        restructured = []
        if results:
            for result in results:
                current_restructured = {}
                for record in result:
                    for key, value in record.items():
                        if key not in current_restructured:
                            current_restructured[key] = []
                        current_restructured[key].append(value)
                restructured.append(current_restructured)
        
        return restructured


    # 執行多筆SQL查詢
    def execute_sql(self, queries):
        try:
            with self.connection.cursor() as cursor:
                results = []
                # 拆分成多個 SQL 語句
                for query in queries:
                    if query.strip():  # 確保語句不為空
                        cursor.execute(query)
                        results.append(cursor.fetchall())
                restructured_results = Database.restructure_data(results)
                return restructured_results
        except pymysql.MySQLError as e:
            return f"SQL query error: {e}"
        finally:
            self.connection.close()


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
    # 取得os env資料
    load_dotenv()
    db_host = os.environ.get('DB_HOST') 
    db_user = os.environ.get('DB_USER') 
    db_password = os.environ.get('DB_PASSWORD') 
    db_name = os.environ.get('DB_NAME')

    db = Database(host = db_host,
                  user = db_user, 
                  password = db_password, 
                  database = db_name,
                  )

    db.connect()
    result = db.execute_sql(sql_query)

    # 判斷查詢結果是否成功
    if "SQL query error" not in result:  # 假設 execute_sql 成功時會返回結果，失敗時可能返回 None 或空列表
        return json.dumps({"status": "查詢成功", "data": result}, default=default_converter, ensure_ascii=False)
    else:
        return json.dumps({"status":"查詢失敗", "message": result}, ensure_ascii=False) # 查詢失敗返回訊息
 
    
# 動態獲取檔案路徑
def get_file_path(relative_path):
    base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# 讀取csv print csv
def csv_read(file_name:str):
    file_path = get_file_path(file_name)
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
