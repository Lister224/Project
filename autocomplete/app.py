from flask import Flask, request, jsonify, render_template
import pandas as pd
import jieba
import re

app = Flask(__name__)

# 關鍵字列表，包含中文
file_path = r'.\keywords.csv'
keywords_pd = pd.read_csv(file_path, header=None)
keywords = keywords_pd[0].tolist()

def extract_search_keywords(query):
    """
    從輸入的句子中提取可能的搜索關鍵字
    """
    # 移除常見的指示詞和年份數字
    common_words = {'我要', '想要', '搜尋', '查詢', '尋找', '年'}
    query = re.sub(r'\d+年?', '', query)  # 移除年份
    
    # 使用結巴分詞
    words = list(jieba.cut(query))
    
    # 過濾掉常見詞
    search_words = [word for word in words if word not in common_words and len(word) > 1]
    
    return search_words

def filter_keywords(query, keywords_list):
    """
    基於提取的搜索關鍵字過濾候選關鍵字
    """
    search_words = extract_search_keywords(query)
    if not search_words:
        return []
        
    filtered_keywords = []
    for keyword in keywords_list:
        # 對於每個搜索詞，檢查是否與關鍵字相關
        for search_word in search_words:
            # 1. 直接包含關係
            if search_word in keyword:
                filtered_keywords.append(keyword)
                break
                
            # 2. 關鍵字的部分匹配（考慮中文詞組）
            keyword_parts = list(jieba.cut(keyword))
            if any(search_word in part for part in keyword_parts):
                filtered_keywords.append(keyword)
                break

    return filtered_keywords

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('query', '')
    if not query:
        return jsonify([])
    
    # 使用改進的過濾邏輯
    filtered_results = filter_keywords(query, keywords)
    
    # 根據相關度排序
    # 1. 完全匹配的關鍵字優先
    # 2. 包含搜索詞的關鍵字次之
    # 3. 關鍵字長度較短的優先
    search_words = extract_search_keywords(query)
    sorted_results = sorted(
        filtered_results,
        key=lambda x: (
            -sum(word in x for word in search_words),  # 匹配的搜索詞數量
            len(x)  # 關鍵字長度
        )
    )
    
    # 限制返回結果數量
    return jsonify(sorted_results[:10])

# 添加自定義詞典（如果有的話）
def init_jieba():
    # 添加常見的財務相關詞彙
    for term in keywords:
        jieba.add_word(term)

if __name__ == '__main__':
    init_jieba()
    app.run(debug=True)