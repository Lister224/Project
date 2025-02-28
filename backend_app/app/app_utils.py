import json
from datetime import datetime
from LLM4sql.mainsql_gemini2 import llm_generate_sql
from app.search_utils import search_terms_with_like_and_match
from analysis.control_chart import create_control_charts
from analysis.forecast import predict_all_indicators
from LLM4report.Genmini_Analysis_new import generate_report
from pymongo import MongoClient
from dotenv import load_dotenv
from concurrent.futures import ProcessPoolExecutor
import os
import pytz

class AppUtils:
    def __init__(self):
        load_dotenv()
        MONGO_URI = os.environ.get('mongo_uri')
        client = MongoClient(MONGO_URI)
        self.db = client["Finvision"]

    # 初始化 question_id
    def init_question_id(self): 
        if self.db.counters.find_one({"_id": "question_id"}) is None:
            self.db.counters.insert_one({"_id": "question_id", "seq": 0}) 

    # 模糊搜尋
    def handle_fuzzy_search(self, input_data):
        keyword = input_data['rows'][0]['keyWord']
        results = search_terms_with_like_and_match(keyword)
        if results:
            suggestions = [result[1] for result in results]
        else:
            suggestions = []
        return suggestions

    # 取得 question_id
    def get_next_question_id(self):
        counter = self.db.counters.find_one_and_update(
            {"_id": "question_id"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True
        )
        return counter["seq"]

    # 解析 & 分類查詢結果
    def parse_and_classify_report(self, query_report_txt):
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

    # 儲存 SQL 查詢結果
    def store_sql_data(self, query_report, query_report_type, question_id, finvision_data, indicator_data):
        query_report['type'] = query_report_type
        if query_report_type == 'finvision':
            data_list = query_report['data']
            indicator_data[question_id] = data_list[0]  # 指標查詢結果
            finvision_data[question_id] = data_list[1:] if len(data_list) > 1 else []
        else:
            return False
        return True

    # 解析 & 儲存使用者查詢
    def handle_full_query(self, input_data, user_inputs, finvision_data, indicator_data, llm_reports):
        rows = input_data['rows']
        question_id = self.get_next_question_id()
        question_date = rows[0]['questionDate']
        question_time = rows[0]['questionTime']
        user_input = rows[0]['questionContent']

        # 調用 LLM 生成 SQL
        query_report_txt = llm_generate_sql(user_input)
        print(f"Generated Query Report: {query_report_txt}")

        if query_report_txt in ['no', 'LLM_error', 'error_search']:
            return query_report_txt, None

        query_report, json_error, query_report_type = self.parse_and_classify_report(query_report_txt)
        if json_error:
            print(f'JSON decoding failed: {json_error}')
            return 'system_error', None

        success = self.store_sql_data(query_report, query_report_type, question_id, finvision_data, indicator_data)
        if not success:
            print('查詢報告暫存錯誤')
            return 'system_error', None

        # **提前生成 LLM 分析報告**
        data = query_report.get('data')
        llm_report = generate_report(data)
        if '生成報告時發生錯誤' in llm_report:
            print("Error generating report.")
            llm_report = 'error'

        # 儲存 LLM 分析報告
        llm_reports[question_id] = llm_report

        # 儲存用戶輸入
        tz = pytz.timezone('Asia/Taipei')
        current_time = datetime.now(tz)
        answer_date = current_time.strftime("%Y-%m-%d")
        answer_time = current_time.strftime("%H:%M:%S")

        user_inputs[question_id] = {
            "question_date": question_date,
            "question_time": question_time,
            "user_input": user_input,
            "answer_date": answer_date,
            "answer_time": answer_time,
            "answer_id": question_id
        }

        # **回傳 LLM 報告，讓前端立即能拿到**
        return question_id, query_report

    # 進行數據分析
    def perform_data_analysis(self, question_id, query_report):
        print(f"[Process {os.getpid()}] 啟動數據分析 - question_id: {question_id}")
        data = query_report.get('data')
        indicator = data[0] if data else None

        if not indicator or indicator == {} or indicator == [{}]:  
            print("Indicator is empty, setting control_chart and forecast to 'error'.")
            control_chart = 'error'
            forecast = 'error'
        else:
            control_chart = create_control_charts(indicator) or 'error'
            forecast = predict_all_indicators(indicator) or 'error'

        return {"control_chart": control_chart, "forecast": forecast}

    # 背景處理
    def background_processing(self, question_id, query_report, analysis_results, llm_reports, 
                              finvision_data, indicator_data, user_inputs):
        print(f"[Background] 啟動數據分析 - question_id: {question_id} (Process: {os.getpid()})")

        try:
            with ProcessPoolExecutor(max_workers=2) as executor:
                future = executor.submit(self.perform_data_analysis, question_id, query_report) #數據分析
                new_analysis_data = future.result()

            # **取出 `llm_report`**
            llm_report = llm_reports.pop(question_id, "error")  # 如果 `llm_report` 不存在，預設為 "error"

            # **合併 `llm_report`、`control_chart` 和 `forecast`**
            analysis_results[question_id] = {
                "question_id": question_id,
                "data": {
                    "llm_report": llm_report,
                    **new_analysis_data
                }
            }

            # **儲存到 MongoDB**
            self.db.user_inputs.replace_one(
                {"question_id": question_id},
                {"question_id": question_id, **user_inputs[question_id]},
                upsert=True
            )

            if question_id in finvision_data:
                self.db.finvision_data.replace_one(
                    {"question_id": question_id},
                    {"question_id": question_id, "data": finvision_data[question_id]},
                    upsert=True
                )

            if question_id in indicator_data:
                self.db.indicator_data.replace_one(
                    {"question_id": question_id},
                    {"question_id": question_id, "data": indicator_data[question_id]},
                    upsert=True
                )

            self.db.analysis_results.update_one(
                {"question_id": question_id},
                {"$set": {
                    "data": analysis_results[question_id]["data"]
                }},
                upsert=True
            )

            print(f"[Background] 數據分析完成 - question_id: {question_id} - 數據已存入 MongoDB")

        except Exception as e:
            print(f"[Background] 錯誤 - question_id: {question_id} - {str(e)}")
