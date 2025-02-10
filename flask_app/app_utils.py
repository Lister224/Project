import json
from datetime import datetime
from LLM4sql.mainsql_gemini2 import llm_generate_sql
from search_utils import search_terms_with_like_and_match
from analysis.control_chart import create_control_charts
from analysis.forecast import predict_all_indicators
from LLM4report.Genmini_Analysis_new import generate_report
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# 初始化 MongoDB 連接
load_dotenv()
MONGO_URI = os.environ.get('mongo_uri')
client = MongoClient(MONGO_URI)
db = client["Finvision"]

# 取得question_id
def get_next_question_id():
    counter = db.counters.find_one_and_update(
        {"_id": "question_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return counter["seq"]


# db查詢結果處理、分類
def parse_and_classify_report(query_report_txt):
    # 去除結果前綴並解析JSON
    try:
        if query_report_txt.startswith('finvision:'):
            query_report_txt = query_report_txt[len('finvision:'):]
            query_report_type = 'finvision'
        else:
            query_report_type = None
        
        query_report = json.loads(query_report_txt)
    except json.JSONDecodeError as e:
        return None, str(e), None
    
    return query_report, None, query_report_type

# 儲存結果資料
def store_sql_data(query_report, query_report_type, question_id, finvision_data, indicator_data):
    query_report['type'] = query_report_type
    if query_report_type == 'finvision':
        data_list = query_report['data']
        indicator_data[question_id] = data_list[0]  # 指標查詢結果
        finvision_data[question_id] = data_list[1:] if len(data_list) > 1 else []
    else:
        return False
    
    return True

# 模糊搜尋
def handle_fuzzy_search(input_data):
    keyword = input_data['rows'][0]['keyWord']
    results = search_terms_with_like_and_match(keyword)
    if results:
        suggestions = [result[1] for result in results]
    else:
        suggestions = []
    return suggestions
    

# 使用者輸入解析、查詢db
def handle_full_query(input_data, user_inputs, finvision_data, analysis_data):
    rows = input_data['rows']
    question_id = get_next_question_id()
    question_date = rows[0]['questionDate']
    question_time = rows[0]['questionTime']
    user_input = rows[0]['questionContent']
    
    # 調用LLM函數生成SQL並執行查詢，返回結果
    query_report_txt = llm_generate_sql(user_input)
    print(f"Generated Query Report: {query_report_txt}")  # 打印生成的查詢報告

    ## 異常報告
    # 處理`no`類型報告
    if query_report_txt == 'no':
        return 'no'
    # LLM連線異常
    if query_report_txt == 'LLM_error':
        return 'LLM_error'
    # 處理錯誤查詢報告
    if query_report_txt == 'error_search':
        return 'error_search'

    # 解析並分類查詢報告
    query_report, json_error, query_report_type = parse_and_classify_report(query_report_txt)
    # json解析錯誤
    if json_error:
        print(f'JSON decoding failed: {json_error}')
        return 'system_error'
   
 
    # 儲存查詢報告數據
    success = store_sql_data(query_report, query_report_type, question_id, finvision_data, analysis_data)
    # 儲存查詢報告錯誤
    if not success:
        print('查詢報告暫存錯誤')
        return 'system_error'
    
    
    # 設置答案生成的日期和時間 
    current_time = datetime.now() 
    answer_date = current_time.strftime("%Y-%m-%d") 
    answer_time = current_time.strftime("%H:%M:%S")

    # 存儲用戶輸入
    user_inputs[question_id] = {
        "question_date": question_date,
        "question_time": question_time,
        "user_input": user_input,
        "answer_date": answer_date,
        "answer_time": answer_time,
        "answer_id": question_id 
    }

    # 返回查詢ID、query_report
    return question_id, query_report

def perform_data_analysis(question_id, query_report, analysis_results):
    data = query_report.get('data')
    indicator = data[0]

    if indicator:  # 指標存在
        # 生成管制圖
        control_chart = create_control_charts(indicator)
        # 判斷是否正常生成資料
        if control_chart is None:
            print("Control chart could not be created.")
            control_chart = 'error'
        # 生成預測點
        forecast = predict_all_indicators(indicator)
        # 判斷是否正常生成資料
        if forecast is None:
            print("Forecast could not be created.")
            forecast = 'error'
    
    else: # 若沒有指標存在
        control_chart = 'error'
        forecast = 'error'
    

    # LLM分析報告生成
    llm_report = generate_report(data)
    # 判斷是否正常生成資料
    if '生成報告時發生錯誤' in llm_report:
        print("Error generating report.")
        llm_report = 'error' 

    # 儲存結果到全局變量
    analysis_results[question_id] = {
        'control_chart': control_chart,
        'forecast': forecast,
        'llm_report': llm_report
    }
    return analysis_results

def background_processing(question_id, query_report, analysis_results, finvision_data, indicator_data, user_inputs):
    try:
        # **執行數據分析**
        analysis_results = perform_data_analysis(question_id, query_report, analysis_results)
        
        # **儲存數據到 MongoDB**
        db.user_inputs.replace_one({"question_id": question_id}, {"question_id": question_id, **user_inputs[question_id]}, upsert=True)
        
        if question_id in finvision_data:
            db.finvision_data.replace_one({"question_id": question_id}, {"question_id": question_id, "data": finvision_data[question_id]}, upsert=True)
        if question_id in indicator_data:
            db.indicator_data.replace_one({"question_id": question_id}, {"question_id": question_id, "data": indicator_data[question_id]}, upsert=True)
        if question_id in analysis_results:
            db.analysis_results.replace_one({"question_id": question_id}, {"question_id": question_id, "data": analysis_results[question_id]}, upsert=True)
        
        print(f"[後台處理完成] question_id: {question_id} - 數據已存入 MongoDB")

    except Exception as e:
        print(f"[異步處理錯誤] {str(e)}")

if __name__ == '__main__':
    input_data = {
            "status": "ok",
            "rows":
            [
                {
                "keyWord":"我要分析毛利率",
                },
            ],
            "msg": ""
            }
    print(handle_fuzzy_search(input_data))


