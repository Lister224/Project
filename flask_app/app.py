from flask import Flask, request, jsonify
from flask_cors import CORS
from app_utils import handle_fuzzy_search, handle_full_query, background_processing
from pymongo import MongoClient
from dotenv import load_dotenv
import multiprocessing
import os
import logging

app = Flask(__name__)
CORS(app)

# 初始化 MongoDB 連接
load_dotenv()
MONGO_URI = os.environ.get('mongo_uri')
client = MongoClient(MONGO_URI)
db = client["Finvision"]

# 初始化 question_id
def init_question_id(): 
    if db.counters.find_one({"_id": "question_id"}) is None:
        db.counters.insert_one({"_id": "question_id", "seq": 0}) 
init_question_id()

# 用於存儲臨時查詢結果的字典
user_inputs = {}
finvision_data = {}
indicator_data = {}
llm_reports = {}
analysis_results = {}

# 根目錄
@app.route('/')
def home():
    return "Hello, World!"


# 使用者輸入問題
@app.route('/query', methods=['POST'])
def query_data():
    logging.info('Received query request')
    input_data = request.get_json()

    # 如果是模糊搜尋請求
    if any('keyWord' in row for row in input_data['rows']):
        suggestions = handle_fuzzy_search(input_data)
        response = {
                "status": "success",
                "msg": "查詢成功",
                 "keyWord":suggestions
            }
        return response

    # 如果是完整查詢請求
    if input_data:
        question_id, query_report = handle_full_query(input_data, user_inputs, finvision_data, indicator_data, llm_reports)
        
        # 判斷是否不為系統支援問題
        if question_id in ['no', 'LLM_error', 'error_search', 'system_error']:
            return jsonify({
                "status": "ng",
                "rows": [],
                "msg": "很抱歉，本系統不支援您的問題!" if question_id == 'no' else 
                       "很抱歉，LLM連線異常，請稍後再試!" if question_id == 'LLM_error' else
                       "很抱歉，本系統資料庫沒有您要查詢的數據!" if question_id == 'error_search' else
                       "很抱歉，本系統異常，請稍後再試!"
            })

        # 多進程執行數據分析、永久儲存
        process = multiprocessing.Process(target=background_processing, 
                                        args=(question_id, query_report,
                                            analysis_results,llm_reports ,finvision_data, 
                                            indicator_data, user_inputs))
        process.start()
            
        # 主執行返回結果
        response = {
            "status": "ok",
            "rows": [
                {
                    "questionId": question_id,
                    "questionDate":user_inputs[question_id]["question_date"],
                    "questionTime":user_inputs[question_id]["question_time"],
                    "questionContent": user_inputs[question_id]["user_input"]
                }
            ],
            "msg": "處理成功"
        }
        print(f"GET questionId: {question_id}")
        logging.info('Query handled successfully')
        return jsonify(response)
    else:
        response = { "status": "ng", 
            "rows": [], 
            "msg": "處理失敗" }
        logging.info('Failed to handle query')
        return jsonify(response)

# 取得指標查詢資料
@app.route('/results/indicator/<int:question_id>', methods=['GET'])
def get_indicator(question_id):
    index_data = indicator_data.get(question_id)
    if index_data:
        response = {
            "status": "ok",
            "rows": [
                {
                    "questionId": question_id,
                    "AnswerId": user_inputs[question_id]["answer_id"],
                    "questionDate": user_inputs[question_id]["question_date"],
                    "questionTime": user_inputs[question_id]["question_time"],
                    "answerDate": user_inputs[question_id]["answer_date"],
                    "answerTime": user_inputs[question_id]["answer_time"],
                    "IndicatorContent": indicator_data
                }
            ],
            "msg": "查詢成功"
        }
        return jsonify(response)
    else:
        return get_history_indicator(question_id)

# 取得現金流量表查詢資料
@app.route('/results/cfs/<int:question_id>', methods=['GET'])
def get_cfs(question_id):
    cfs_data = finvision_data.get(question_id, [])[0] if finvision_data.get(question_id) else None  # 第一個list
    if cfs_data:
      
        # 將現有的 CFS 內容封裝到前端要求的格式中
        response = {
            "status": "ok",
            "rows": [
                {
                    "questionId": question_id,
                    "AnswerId": user_inputs[question_id]["answer_id"],   # 從 user_inputs 獲取answer_id
                    "questionDate": user_inputs[question_id]["question_date"],  # 從 user_inputs 獲取日期
                    "questionTime": user_inputs[question_id]["question_time"],  # 從 user_inputs 獲取時間
                    "answerDate": user_inputs[question_id]["answer_date"],  # 從 user_inputs 獲取答案日期
                    "answerTime": user_inputs[question_id]["answer_time"],  # 從 user_inputs 獲取答案時間
                    "CFSContent": cfs_data  # 將 CFS 內容封裝到 CFSContent 中
                }
            ],
            "msg": "查詢成功"
        }
        return jsonify(response)

    else: 
        return get_history_cfs(question_id)

# 取得資產負債表查詢資料
@app.route('/results/bs/<int:question_id>', methods=['GET'])
def get_bs(question_id):
    bs_data = finvision_data.get(question_id, [])[1] if finvision_data.get(question_id) else None  # 第二個list
    if bs_data:
        # 將現有的 BS 內容封裝到前端要求的格式中
        response = {
            "status": "ok",
            "rows": [
                {
                    "questionId": question_id,
                    "AnswerId": user_inputs[question_id]["answer_id"],   # 從 user_inputs 獲取answer_id
                    "questionDate": user_inputs[question_id]["question_date"],  # 從 user_inputs 獲取日期
                    "questionTime": user_inputs[question_id]["question_time"],  # 從 user_inputs 獲取時間
                    "answerDate": user_inputs[question_id]["answer_date"],  # 從 user_inputs 獲取答案日期
                    "answerTime": user_inputs[question_id]["answer_time"],  # 從 user_inputs 獲取答案時間
                    "BSContent": bs_data  # 將 CFS 內容封裝到 CFSContent 中
                }
            ],
            "msg": "查詢成功"
        }
        return jsonify(response)

    else: 
        return get_history_bs(question_id)
    
# 取得損益表查詢資料
@app.route('/results/pl/<int:question_id>', methods=['GET'])
def get_pl(question_id):
    pl_data = finvision_data.get(question_id, [])[2] if finvision_data.get(question_id) else None  # 第三個list
    if pl_data:
        # 將現有的 PL 內容封裝到前端要求的格式中
        response = {
            "status": "ok",
            "rows": [
                {
                    "questionId": question_id,
                    "AnswerId": user_inputs[question_id]["answer_id"],   # 從 user_inputs 獲取answer_id
                    "questionDate": user_inputs[question_id]["question_date"],  # 從 user_inputs 獲取日期
                    "questionTime": user_inputs[question_id]["question_time"],  # 從 user_inputs 獲取時間
                    "answerDate": user_inputs[question_id]["answer_date"],  # 從 user_inputs 獲取答案日期
                    "answerTime": user_inputs[question_id]["answer_time"],  # 從 user_inputs 獲取答案時間
                    "PLContent": pl_data  # 將 CFS 內容封裝到 CFSContent 中
                }
            ],
            "msg": "查詢成功"
        }
        return jsonify(response)

    else: 
        return get_history_pl(question_id)
    
# 取得管制圖點位數據
@app.route('/results/control-chart/<int:question_id>', methods=['GET']) 
def get_control_chart(question_id):
    control_chart = analysis_results.get(question_id, {}).get('control_chart') 
    if control_chart == 'error':
            response = {"status": "ng", 
            "rows": [], 
            "msg": "No control_chart data found for the given question_id" }

    elif control_chart:
        response = {
            "status": "ok",
            "rows": [
                {
                    "questionId": question_id,
                    "questionDate": user_inputs[question_id]["question_date"],  # 從 user_inputs 獲取日期
                    "questionTime": user_inputs[question_id]["question_time"],  # 從 user_inputs 獲取時間
                    "answerId": question_id,
                    "answerDate": user_inputs[question_id]["answer_date"],  # 從 user_inputs 獲取答案日期
                    "answerTime": user_inputs[question_id]["answer_time"],  # 從 user_inputs 獲取答案時間
                    "plotContent": control_chart
                }
            ],
            "msg": "查詢成功"
        }
    else:
        return get_history_control_chart(question_id)
    

    return jsonify(response)

# 取得預測點位數據
@app.route('/results/forecast/<int:question_id>', methods=['GET']) 
def get_forecast(question_id): 
    forecast = analysis_results.get(question_id, {}).get('forecast') 
    if forecast == 'error':
        response = {"status": "ng", 
            "rows": [], 
            "msg": "No forecast data found for the given question_id"}
    elif forecast:
        response = {
            "status": "ok",
             "rows": [               
                {
                    "questionId": question_id,
                    "questionDate": user_inputs[question_id]["question_date"],  # 從 user_inputs 獲取日期
                    "questionTime": user_inputs[question_id]["question_time"],  # 從 user_inputs 獲取時間
                    "answerId": question_id,
                    "answerDate": user_inputs[question_id]["answer_date"],  # 從 user_inputs 獲取答案日期
                    "answerTime": user_inputs[question_id]["answer_time"],  # 從 user_inputs 獲取答案時間
                    "forecastContent": forecast
                }
            ],
            "msg": "查詢成功"
        }
    else:
        return get_history_forecast(question_id)
    return jsonify(response)

# 取得分析報告數據
@app.route('/results/report/<int:question_id>', methods=['GET']) 
def get_report(question_id): 
    # **先從 `llm_reports` 取值**
    if question_id in llm_reports:
        report = llm_reports[question_id]
    else:
        # **再從 MongoDB 取值**
        return get_history_llm_report(question_id)

    if not report:
        return jsonify({"status": "pending", "rows": [], "msg": "LLM 分析報告尚在生成中!"})

    if report == 'error':
        response = {"status": "ng", "rows": [], "msg": "LLM 分析報告生成異常!"}
    else:
        response = {
            "status": "ok",
            "rows": [
                {
                    "questionId": question_id,
                    "questionDate": user_inputs.get(question_id, {}).get("question_date", ""),
                    "questionTime": user_inputs.get(question_id, {}).get("question_time", ""),
                    "questionContent": user_inputs.get(question_id, {}).get("user_input", ""),
                    "answerId": question_id,
                    "answerDate": user_inputs.get(question_id, {}).get("answer_date", ""),
                    "answerTime": user_inputs.get(question_id, {}).get("answer_time", ""),
                    "answerContent": report
                }
            ],
            "msg": "查詢成功"
        }
    return jsonify(response)


### 歷史資料取得端點
# 取得指標歷史紀錄
@app.route('/history_results/indicator/<int:question_id>', methods=['GET'])
def get_history_indicator(question_id):
    # 使用者提問資料
    collection_1 = db['user_inputs'] 
    # 指標資料
    collection_2 = db['indicator_data'] 

    # 查找資料，根據 question_id 相等
    user_inputs = collection_1.find_one(
        {'question_id': question_id})
    indicator_data = collection_2.find_one(
        {'question_id': question_id},
        {'data': 1, '_id': 0})
    
    history_indicator = indicator_data['data'] if indicator_data else {}
    if history_indicator:
        response = {
            "status": "ok",
            "rows": [
                {
                    "questionId": question_id,
                    "AnswerId": user_inputs["answer_id"],
                    "questionDate": user_inputs["question_date"],
                    "questionTime": user_inputs["question_time"],
                    "answerDate": user_inputs["answer_date"],
                    "answerTime": user_inputs["answer_time"],
                    "IndicatorContent": history_indicator
                }
            ],
            "msg": "查詢成功"
        }
    else:
        response = {
            "status": "ng",
            "rows": [],
            "msg": "No Indicator data found for the given question_id"
        }
    return jsonify(response)

# 取得cfs歷史紀錄
@app.route('/history_results/cfs/<int:question_id>', methods=['GET'])
def get_history_cfs(question_id):
    # 使用者提問資料
    collection_1 = db['user_inputs'] 
    # 指標資料
    collection_2 = db['finvision_data'] 

    # 查找資料，根據 question_id 相等
    user_inputs = collection_1.find_one(
        {'question_id': question_id})
    cfs_data = collection_2.find_one(
        {'question_id': question_id},
        {'data': 1, '_id': 0})
    
    history_cfs = cfs_data['data'][0] if cfs_data else {}
    if history_cfs:
        response = {
            "status": "ok",
            "rows": [
                {
                    "questionId": question_id,
                    "AnswerId": user_inputs["answer_id"],
                    "questionDate": user_inputs["question_date"],
                    "questionTime": user_inputs["question_time"],
                    "answerDate": user_inputs["answer_date"],
                    "answerTime": user_inputs["answer_time"],
                    "CFSContent": history_cfs
                }
            ],
            "msg": "查詢成功"
        }
    else:
        response = {
            "status": "ng",
            "rows": [],
            "msg": "No CFS data found for the given question_id"
        }
    return jsonify(response)

# 取得bs歷史紀錄
@app.route('/history_results/bs/<int:question_id>', methods=['GET'])
def get_history_bs(question_id):
    # 使用者提問資料
    collection_1 = db['user_inputs'] 
    # 指標資料
    collection_2 = db['finvision_data'] 

    # 查找資料，根據 question_id 相等
    user_inputs = collection_1.find_one(
        {'question_id': question_id})
    bs_data = collection_2.find_one(
        {'question_id': question_id},
        {'data': 1, '_id': 0})
    
    history_bs = bs_data['data'][1] if bs_data else {}
    if history_bs:
        response = {
            "status": "ok",
            "rows": [
                {
                    "questionId": question_id,
                    "AnswerId": user_inputs["answer_id"],
                    "questionDate": user_inputs["question_date"],
                    "questionTime": user_inputs["question_time"],
                    "answerDate": user_inputs["answer_date"],
                    "answerTime": user_inputs["answer_time"],
                    "BSContent": history_bs
                }
            ],
            "msg": "查詢成功"
        }
    else:
        response = {
            "status": "ng",
            "rows": [],
            "msg": "No BS data found for the given question_id"
        }
    return jsonify(response)

# 取得pl歷史紀錄
@app.route('/history_results/pl/<int:question_id>', methods=['GET'])
def get_history_pl(question_id):
    # 使用者提問資料
    collection_1 = db['user_inputs'] 
    # 指標資料
    collection_2 = db['finvision_data'] 

    # 查找資料，根據 question_id 相等
    user_inputs = collection_1.find_one(
        {'question_id': question_id})
    pl_data = collection_2.find_one(
        {'question_id': question_id},
        {'data': 1, '_id': 0})
    
    history_pl = pl_data['data'][2] if pl_data else {}
    if history_pl:
        response = {
            "status": "ok",
            "rows": [
                {
                    "questionId": question_id,
                    "AnswerId": user_inputs["answer_id"],
                    "questionDate": user_inputs["question_date"],
                    "questionTime": user_inputs["question_time"],
                    "answerDate": user_inputs["answer_date"],
                    "answerTime": user_inputs["answer_time"],
                    "PLContent": history_pl
                }
            ],
            "msg": "查詢成功"
        }
    else:
        response = {
            "status": "ng",
            "rows": [],
            "msg": "No PL data found for the given question_id"
        }
    return jsonify(response)

# 取得control_chart歷史紀錄
@app.route('/history_results/control-chart/<int:question_id>', methods=['GET'])
def get_history_control_chart(question_id):
    # 使用者提問資料
    collection_1 = db['user_inputs'] 
    # 指標資料
    collection_2 = db['analysis_results'] 

    # 查找資料，根據 question_id 相等
    user_inputs = collection_1.find_one(
        {'question_id': question_id})
    control_chart_data = collection_2.find_one(
        {'question_id': question_id})
    
    history_control_chart = control_chart_data['data']['control_chart'] if control_chart_data else {}
    # 當時無資料或生成失敗
    if history_control_chart == 'error':
            response = {"status": "ng", 
            "rows": [], 
            "msg": "No control_chart data found for the given question_id" }
    # 當時有資料  
    elif history_control_chart:
        response = {
            "status": "ok",
            "rows": [
                {
                    "questionId": question_id,
                    "AnswerId": user_inputs["answer_id"],
                    "questionDate": user_inputs["question_date"],
                    "questionTime": user_inputs["question_time"],
                    "answerDate": user_inputs["answer_date"],
                    "answerTime": user_inputs["answer_time"],
                    "plotContent": history_control_chart
                }
            ],
            "msg": "查詢成功"
        }
    # 無紀錄，現在生成中
    else:
        response = {
            "status": "pending",
            "rows": [],
            "msg": "管制圖尚在產生中!"
        }
    return jsonify(response)

# 取得forecast歷史紀錄
@app.route('/history_results/forecast/<int:question_id>', methods=['GET'])
def get_history_forecast(question_id):
    # 使用者提問資料
    collection_1 = db['user_inputs'] 
    # 指標資料
    collection_2 = db['analysis_results'] 

    # 查找資料，根據 question_id 相等
    user_inputs = collection_1.find_one(
        {'question_id': question_id})
    forecast_data = collection_2.find_one(
        {'question_id': question_id})
    
    history_forecast = forecast_data['data']['forecast'] if forecast_data else {}
    # 當時無資料或生成失敗
    if history_forecast == 'error':
        response = {"status": "ng", 
            "rows": [], 
            "msg": "No forecast data found for the given question_id"}
    # 當時有資料
    elif history_forecast:
        response = {
            "status": "ok",
            "rows": [
                {
                    "questionId": question_id,
                    "AnswerId": user_inputs["answer_id"],
                    "questionDate": user_inputs["question_date"],
                    "questionTime": user_inputs["question_time"],
                    "answerDate": user_inputs["answer_date"],
                    "answerTime": user_inputs["answer_time"],
                    "forecastContent": history_forecast
                }
            ],
            "msg": "查詢成功"
        }
    # 無紀錄，現在生成中
    else:
        response = {
            "status": "pending",
            "rows": [],
            "msg": "指標預測尚在產生中!"
        }
    return jsonify(response)

# 取得llm_report歷史紀錄
@app.route('/history_results/report/<int:question_id>', methods=['GET'])
def get_history_llm_report(question_id):
    # 使用者提問資料
    collection_1 = db['user_inputs'] 
    # 指標資料
    collection_2 = db['analysis_results'] 

    # 查找資料，根據 question_id 相等
    user_inputs = collection_1.find_one(
        {'question_id': question_id})
    llm_report_data = collection_2.find_one(
        {'question_id': question_id})
    
    history_llm_report = llm_report_data['data']['llm_report'] if llm_report_data else {}
    # 當時無資料或生成失敗
    if history_llm_report == 'error':
        response = {"status": "ng", 
        "rows": [], 
        "msg": "LLM分析報告生成異常!"}
    # 當時有資料
    elif history_llm_report:
        response = {
            "status": "ok",
            "rows": [
                {
                    "questionId": question_id,
                    "AnswerId": user_inputs["answer_id"],
                    "questionDate": user_inputs["question_date"],
                    "questionTime": user_inputs["question_time"],
                    "answerDate": user_inputs["answer_date"],
                    "answerTime": user_inputs["answer_time"],
                    "answerContent": history_llm_report
                }
            ],
            "msg": "查詢成功"
        }
    # 無紀錄，現在生成中
    else:
        response = {
            "status": "pending",
            "rows": [],
            "msg": "LLM分析報告尚在生成中!"
        }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=8080)
