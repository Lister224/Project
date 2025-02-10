from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from app_utils import handle_fuzzy_search, handle_full_query, background_processing
from pymongo import MongoClient
from dotenv import load_dotenv
import threading
import os


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
analysis_results = {}

# 根目錄
@app.route('/')
def home():
    return "Hello, World!"


# 使用者輸入問題
@app.route('/query', methods=['POST'])
def query_data():
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
        question_id, query_report = handle_full_query(input_data, user_inputs, finvision_data, indicator_data)
        
        # 判斷是否不為系統支援問題
        if question_id == 'no':
            response = {"status": "ng", 
            "rows": [], 
            "msg": "很抱歉，本系統不支援您的問題!" }
            return jsonify(response)
        # 判斷LLM連線異常
        if question_id == 'LLM_error':
            response = {"status": "ng", 
            "rows": [], 
            "msg": "很抱歉，LLM連線異常，請稍後再試!" }
            return jsonify(response)
        # 判斷查詢錯誤
        if question_id == 'error_search':
            response = {"status": "ng", 
            "rows": [], 
            "msg": "很抱歉，本系統資料庫沒有您要查詢的數據!" }
            return jsonify(response)
        # 判斷系統錯誤
        if question_id == 'system_error':
            response = {"status": "ng", 
            "rows": [], 
            "msg": "很抱歉，本系統異常，請稍後再試!" }
            return jsonify(response)

        # 異步執行數據分析、永久儲存
        threading.Thread(target=background_processing, 
                         args=(question_id, query_report, 
                               analysis_results, finvision_data, 
                               indicator_data, user_inputs)).start()

               
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
        return jsonify(response)

    else:
        response = { "status": "ng", 
            "rows": [], 
            "msg": "處理失敗" }
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
    else:
        response = {
            "status": "ng",
            "rows": [],
            "msg": "No Indicator data found for the given question_id"
        }
    return jsonify(response)


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

    else: 
        response = { "status": "ng", 
                    "rows": [], 
                    "msg": "No CFS data found for the given question_id" }
    
    return jsonify(response)


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

    else: 
        response = { "status": "ng", 
                    "rows": [], 
                    "msg": "No BS data found for the given question_id" }
    
    return jsonify(response)

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

    else: 
        response = {"status": "ng", 
                    "rows": [], 
                    "msg": "No PL data found for the given question_id" }
    
    return jsonify(response)


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
        response = {"status": "pending", 
            "rows": [], 
            "msg": "管制圖尚在產生中!" }
    

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
        response = {"status": "pending", 
            "rows": [], 
            "msg": "指標預測尚在產生中!" }
    return jsonify(response)

# 取得llm生成文字報告
@app.route('/results/report/<int:question_id>', methods=['GET']) 
def get_report(question_id): 
    report = analysis_results.get(question_id, {}).get('llm_report')
    if report == 'error':
            response = {"status": "ng", 
            "rows": [], 
            "msg": "LLM分析報告生成異常!" }
    elif report:
        response = {
            "status": "ok",
            "rows": [
                {
                    "questionId": question_id,
                    "questionDate": user_inputs[question_id]["question_date"],  # 從 user_inputs 獲取日期
                    "questionTime": user_inputs[question_id]["question_time"],  # 從 user_inputs 獲取時間
                    "questionContent":user_inputs[question_id]["user_input"], # 從 user_inputs 獲取提問
                    "answerId": question_id,
                    "answerDate": user_inputs[question_id]["answer_date"],  # 從 user_inputs 獲取答案日期
                    "answerTime": user_inputs[question_id]["answer_time"],  # 從 user_inputs 獲取答案時間
                    "answerContent": report
                }
            ],
            "msg": "查詢成功"
        }
    else:
        response = {"status": "pending", 
            "rows": [], 
            "msg": "LLM分析報告尚在生成中!" }


    return jsonify(response)



# # 保留模糊搜尋額外端點
# @app.route('/search', methods=['GET'])
# def search():
#     keyword = request.args.get('keyword', '').strip()
#     if keyword:
#         results = search_terms_with_like_and_match(keyword)
#         return jsonify(results)
#     else:
#         return jsonify({"message": "Keyword is required"}), 400


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=8080)
