import json
from flask import jsonify
from datetime import datetime
from LLM4sql.mainsql_gemini2 import llm_generate_sql
from search_utils import search_terms_with_like_and_match
from analysis.control_chart import create_control_charts
from LLM4report.Genmini_Analysis_new import generate_report


# 處理不屬於系統支援問題
def handle_no():
    return 'no'

# db查詢結果處理、分類
def parse_and_classify_report(query_report_str):
    # 去除結果前綴並解析JSON
    try:
        if query_report_str.startswith('finvision:'):
            query_report_str = query_report_str[len('finvision:'):]
            query_report_type = 'finvision'
        elif query_report_str.strip() == 'no':  # 修正這裡
            query_report_type = 'no'
            return None, None, query_report_type  # 直接返回，不進行JSON解析
        else:
            query_report_type = None
        
        query_report = json.loads(query_report_str)
    except json.JSONDecodeError as e:
        return None, str(e), None
    
    return query_report, None, query_report_type

# 儲存結果資料
def store_sql_data(query_report, query_report_type, question_id, query_reports, finvision_data, indicator_data):
    query_report['type'] = query_report_type
    if query_report_type == 'finvision':
        query_reports[question_id] = query_report
        data_list = query_report['data']
        indicator_data[question_id] = data_list[0]  # 指標查詢結果
        finvision_data[question_id] = data_list[1:] if len(data_list) > 1 else []
    else:
        return False
    
    return True

# 模糊搜尋
def handle_fuzzy_search(input_data):
    keyword = input_data['search_suggestions']
    results = search_terms_with_like_and_match(keyword)
    return jsonify({"suggestions": results})

# 使用者輸入解析、查詢db
def handle_full_query(input_data, query_reports, user_inputs, finvision_data, analysis_data):
    rows = input_data['rows']
    question_id = rows[0]['questionId']
    question_date = rows[0]['questionDate']
    question_time = rows[0]['questionTime']
    user_input = rows[0]['questionContent']
    
    # 調用LLM函數生成SQL並執行查詢，返回結果
    query_report_str = llm_generate_sql(user_input)
    print(f"Generated Query Report: {query_report_str}")  # 打印生成的查詢報告

    # 解析並分類查詢報告
    query_report, json_error, query_report_type = parse_and_classify_report(query_report_str)
    if json_error:
        return jsonify({'message': f'JSON decoding failed: {json_error}'}), 500

    # 處理`no`類型報告
    if query_report_type == 'no':
        return 'no'

    # 儲存查詢報告數據
    success = store_sql_data(query_report, query_report_type, question_id, query_reports, finvision_data, analysis_data)
    if not success:
        return jsonify({'message': 'Unexpected error occurred.'}), 500
    
    # 設置答案生成的日期和時間 
    current_time = datetime.now() 
    answer_date = current_time.strftime("%Y-%m-%d") 
    answer_time = current_time.strftime("%H:%M:%S")

    # 存儲用戶輸入
    user_inputs[question_id] = {
        "question_date": question_date,
        "question_time": question_time,
        "user_input": user_input,
        "answer_date": answer_date, # 初始化為空 
        "answer_time": answer_time, # 初始化為空 
        "answer_id": question_id # 初始化為空
    }

    # 返回查詢ID給用戶
    return question_id

def perform_data_analysis(question_id, query_report, analysis_results):
    data = query_report.get('data')
    #control_chart = create_control_charts(data[0])
    # forecast = generate_forecast(data[0])
    llm_report = generate_report(data)
    # 將結果存儲到全局變量
    analysis_results[question_id] = {
        #'control_chart': control_chart,
        # 'forecast': forecast,
        'llm_report': llm_report
    }





