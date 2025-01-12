from flask import Flask, request, jsonify
from LLM4sql.mainsql_gemini2 import llm_generate_sql
from app_utils import handle_no,handle_analysis,handle_finvision

app = Flask(__name__)

# 用於存儲臨時查詢結果的字典
query_reports = {}
user_inputs = {}
analysis_reports = {}

@app.route('/query', methods=['POST'])
def query_data():
    input_data = request.get_json()
    user_input = input_data.get('user_input')
    
    # 調用LLM函式生成SQL並執行查詢
    query_report = llm_generate_sql(user_input)
    # 根據報告進行分類並調用對應的處理函數
    if 'no' in query_report: 
        analysis_report = handle_no()
    elif 'analysis' in query_report: 
        analysis_report = handle_analysis(query_report) 
    elif 'finvision' in query_report: 
        analysis_report = handle_finvision(query_report)
    else: 
        return jsonify({'message': 'Unexpected error occurred.'})
    
    # 存儲查詢結果、分析報告和user_input並生成查詢ID
    query_id = len(query_reports) + 1
    query_reports[query_id] = query_report
    analysis_reports[query_id] = analysis_report
    user_inputs[query_id] = user_input

    # 返回查詢ID給用戶
    return jsonify({"query_id": query_id})

@app.route('/results/<int:query_id>', methods=['GET'])
def get_results(query_id):
    query_report = query_reports.get(query_id)
    user_input = user_inputs.get(query_id)
    analysis_report = analysis_reports.get(query_id)
    
    if query_report and analysis_report:
        return jsonify({
            "user_input": user_input,
            "query_result": query_report,
            "analysis_report": analysis_report
        })
    else:
        return jsonify({"message": "No results found for the given query_id"}), 404

if __name__ == '__main__':
    app.run(debug=True)




    

