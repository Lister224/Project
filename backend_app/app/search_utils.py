import os
import pymysql
from dotenv import load_dotenv


def remove_prefix(keyword, prefix_list):
    for prefix in prefix_list:
        if keyword.startswith(prefix):
            return keyword[len(prefix):]
    return keyword

def remove_years(keyword):
    import re
    return re.sub(r'\d{4}', '', keyword)

def search_terms_with_like_and_match(keyword):
    # 前綴詞列表
    prefix_list = ["我要分析","我想查詢", "請幫我查詢", "能否查詢", 
                   "我想分析", "幫我分析", "請幫我分析", "分析",'查詢'
                   "第一季", "第二季", "第三季", "第四季"]

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

    load_dotenv()
    db_host = os.environ.get('DB_HOST')
    db_user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')
    db_name = os.environ.get('DB_NAME')

    connection = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
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
    print(results)

