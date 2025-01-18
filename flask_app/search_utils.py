import pymysql
import re

def remove_prefix(text, prefix_list):
    for prefix in prefix_list:
        if text.startswith(prefix):
            return text[len(prefix):].strip()
    return text

def remove_years(text):
    # 使用正則表達式去除年份
    return re.sub(r'\d{4}年?', '', text).strip()

def search_terms_with_like_and_match(keyword):
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'el89829603',
        'database': 'finvision'
    }

    # 前綴詞列表
    prefix_list = ["我想查詢", "請幫我查詢", "能否查詢", 
                   "我想分析", "幫我分析", "第一季", 
                   "第二季", "第三季", "第四季"]

    # 去除前綴詞
    keyword = remove_prefix(keyword, prefix_list)

    # 去除數字年份
    keyword = remove_years(keyword)

    query = f"""
    SELECT terms, related_term
    FROM searching
    WHERE MATCH(terms, related_term) AGAINST ('{keyword}' IN NATURAL LANGUAGE MODE)
      OR terms LIKE '%{keyword}%'
      OR related_term LIKE '%{keyword}%';
    """

    connection = pymysql.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database']
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            return results
    finally:
        connection.close()

# 測試
if __name__ == "__main__":
    keyword = input("請輸入要查詢的關鍵字: ")
    results = search_terms_with_like_and_match(keyword)
    # 顯示結果
    for term, related in results:
        print(f"Terms: {term}, Related: {related}")
