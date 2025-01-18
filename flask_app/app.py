from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from app_utils import handle_fuzzy_search, handle_full_query, perform_data_analysis
from search_utils import search_terms_with_like_and_match
import threading

app = Flask(__name__)
CORS(app)

# 用於存儲臨時查詢結果的字典
query_reports = {}
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
    if 'EnterText' in input_data:
        return handle_fuzzy_search(input_data)

    # 如果是完整查詢請求
    if input_data['status'] == 'ok':
        question_id = handle_full_query(input_data, query_reports, user_inputs, finvision_data, indicator_data)
        
        # 判斷是否不為系統支援問題
        if question_id == 'no':
            response = {"status": "error", 
            "rows": [], 
            "msg": "很抱歉，本系統不支援您的問題!" }
            return jsonify(response)

        # 異步執行數據分析
        query_report = query_reports[question_id]
        threading.Thread(target=perform_data_analysis, args=(question_id, query_report, analysis_results)).start()

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
        response = { "status": "error", 
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
            "status": "error",
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
        response = { "status": "error", 
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
        response = { "status": "error", 
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
        response = {"status": "error", 
                    "rows": [], 
                    "msg": "No PL data found for the given question_id" }
    
    return jsonify(response)


# 取得管制圖點位數據
@app.route('/results/control-chart/<int:question_id>', methods=['GET']) 
def get_control_chart(question_id): 
    control_chart = analysis_results.get(question_id, {}).get('control_chart') 
    if control_chart: 
        return jsonify(control_chart) 
    else: 
        return jsonify({"message": "No Control Chart data found for the given question_id"}), 404

# 取得預測點位數據
@app.route('/results/forecast/<int:question_id>', methods=['GET']) 
def get_forecast(question_id): 
    forecast = analysis_results.get(question_id, {}).get('forecast') 
    if forecast: 
        return jsonify(forecast) 
    else: 
        return jsonify({"message": "No Forecast data found for the given question_id"}),404

# 取得llm生成文字報告
@app.route('/results/report/<int:question_id>', methods=['GET']) 
def get_report(question_id): 
    report = analysis_results.get(question_id, {}).get('llm_report') 
    if report:
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
        response = {"status": "error", 
            "rows": [], 
            "msg": "No Report data found for the given question_id" }
    return jsonify(response)


# 保留模糊搜尋額外端點
@app.route('/search', methods=['GET'])
def search():
    keyword = request.args.get('keyword', '').strip()
    if keyword:
        results = search_terms_with_like_and_match(keyword)
        return jsonify(results)
    else:
        return jsonify({"message": "Keyword is required"}), 400


if __name__ == '__main__':
    app.run(debug=True, port=8080)
