from flask import Flask, request, jsonify
from flask_cors import CORS
from forecast import predict_all_indicators  # 引入你的預測函式

app = Flask(__name__)
CORS(app)


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json  # 取得前端傳來的 JSON
        if not data:
            return jsonify({"error": "請提供數據"}), 400

        predictions = predict_all_indicators(data)
        return jsonify({"predictions": predictions})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
