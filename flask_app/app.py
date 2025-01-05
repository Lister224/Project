from flask import Flask, request, jsonify
from LLM4sql.mainsql_gemini2.0 import classify_user_input

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/api/classify', methods=['POST'])
def user_input():
    # 從 JSON 請求中提取 'user_input'
    user_input_json = request.json
    user_input_str = user_input_json.get('user_input', '')
    # 傳給 LLM 判斷
    report = classify_user_input(user_input_str)
    return report






if __name__ == '__main__':
    app.run(debug=True)
