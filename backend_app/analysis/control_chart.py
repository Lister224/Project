import os
import pandas as pd
import pymysql
from dotenv import load_dotenv

# db功能設計
class Database:
    def __init__(self, host, user, password, database, charset='utf8mb4'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.connection = None

    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset=self.charset,
                cursorclass=pymysql.cursors.DictCursor
            )
            
        except pymysql.MySQLError as e:
            print(f"帳密或資料庫、伺服器輸入錯誤: {e}")
            self.connection = None

    def execute_query(self, query):
        if not self.connection:
            print("沒有可用的資料庫連線")
            return None
        
        try:
            with self.connection.cursor() as cursor:
                if query.strip():
                    cursor.execute(query)
                    result = cursor.fetchall()
                    return result
        except pymysql.MySQLError as e:
            print(f"SQL query error: {e}")
            return None

    def close(self):
        if self.connection and self.connection.open:
            self.connection.close()
            

# 獲取db資料
def get_data(column_name: str):
    sql_query = f'''
        SELECT seasons, {column_name}
        FROM (
            SELECT seasons, {column_name}
            FROM indicators
            ORDER BY seasons DESC
            LIMIT 16
        ) sub
        ORDER BY seasons ASC;
    '''
    load_dotenv()
    db_host = os.environ.get('DB_HOST') 
    db_user = os.environ.get('DB_USER') 
    db_password = os.environ.get('DB_PASSWORD') 
    db_name = os.environ.get('DB_NAME')

    db = Database(host = db_host,
                  user = db_user, 
                  password = db_password, 
                  database = db_name,
                  )
    db.connect()
    result = db.execute_query(sql_query)
    db.close()
    return(result)

# 獲取指標名
def get_column_name(index_data):
    if isinstance(index_data, dict) and len(index_data) > 0:
        # 使用列表推導式來過濾 key
        keys = [key for key in index_data.keys() if key != 'seasons']
        return keys
    else:
        return []

# 管制圖點位數據運算
def create_control_charts(index_data):
    """
    為每個欄位創建管制圖數據
    
    Args:
        index_data: 輸入數據
    Returns:
        dict: 每個欄位的管制圖數據
    """
    columns = get_column_name(index_data)  # 獲取所有欄位名稱

    all_charts = {}

    # 新增 "name" 列表
    all_charts['name'] = columns
    
    for column_name in columns:
        result = get_data(column_name)
        
        # 轉為 DataFrame
        df = pd.DataFrame(result)
        
        # 設定 EMA 的衰減因子
        span = 3
        
        # 計算指數加權移動平均值和標準差
        df['ema'] = df[column_name].ewm(span=span, adjust=False).mean()
        df['emsd'] = df[column_name].ewm(span=span, adjust=False).std()
        
        # 計算1σ, 2σ 和 3σ (UCL 和 LCL) 控制限
        k = [1, 2, 3]
        for sigma in k:
            df[f'UCL_{sigma}sigma'] = df['ema'] + (sigma * df['emsd'])
            df[f'LCL_{sigma}sigma'] = df['ema'] - (sigma * df['emsd'])
        
        # 移除前兩筆資料
        df = df.iloc[3:]
        
        # 準備每個欄位的結果
        # 準備每個欄位的結果 
        chart_data = {
            'seasons': df['seasons'].tolist(), 
            column_name: df[column_name].tolist(), 
            'ema': df['ema'].tolist(), 
            'UCL_1sigma': df['UCL_1sigma'].tolist(), 
            'LCL_1sigma': df['LCL_1sigma'].tolist(), 
            'UCL_2sigma': df['UCL_2sigma'].tolist(), 
            'LCL_2sigma': df['LCL_2sigma'].tolist(), 
            'UCL_3sigma': df['UCL_3sigma'].tolist(), 
            'LCL_3sigma': df['LCL_3sigma'].tolist()}
        
        all_charts[column_name] = chart_data
    print('生成管制圖')
    return all_charts

def plot_control_chart(chart_data, column_name):
    import matplotlib.pyplot as plt

    # 將數據轉換回 DataFrame
    df = pd.DataFrame(chart_data)

    # 創建圖表和子圖
    fig, ax = plt.subplots(figsize=(12, 5))

    # 繪製原始數據和 EMA
    ax.plot(df['seasons'], df[column_name], 'k.-', label='Raw Data')
    ax.plot(df['seasons'], df['ema'], 'm--', label='EMA')

    # 繪製控制限
    control_limits = [
        {'sigma': 3, 'color': 'red', 'style': '-'},
        {'sigma': 2, 'color': 'orange', 'style': ':'},
        {'sigma': 1, 'color': 'green', 'style': ':'}
    ]
    for limit in control_limits:
        sigma = limit['sigma']
        color = limit['color']
        style = limit['style']

        # 繪製上下限
        ax.plot(df['seasons'], df[f'UCL_{sigma}sigma'], color=color, linestyle=style, label=f'+{sigma}σ')
        ax.plot(df['seasons'], df[f'LCL_{sigma}sigma'], color=color, linestyle=style, label=f'-{sigma}σ')

    # 設置標題和標籤
    ax.set_title(f'Control Chart - {column_name}')
    ax.set_xlabel('Seasons')
    ax.set_ylabel('Value')
    ax.grid(True, linestyle='--', alpha=0.7)

    # 旋轉 x 軸標籤以避免重疊
    ax.tick_params(axis='x', rotation=45)

    # 添加圖例
    ax.legend()

    # 調整布局以確保所有元素都顯示完整
    plt.tight_layout()

    # 顯示圖表
    plt.show()

if __name__ == '__main__':
    columns = get_column_name({'seasons': ['2024Q1', '2024Q2', '2024Q3'], 'GPM': [53.07, 53.17, 57.83], 'OPM': [42.02, 42.55, 47.49], 'NPM': [38.0, 36.77, 42.79], 'ROE_Q': [6.3, 6.62, 8.29], 'ROA_Q': [3.98, 4.21, 5.35], 'RGR_Q': [-5.26, 13.64, 12.8], 'TAGR_Q': [4.62, 3.36, 3.06], 'LTDR': [16.68, 16.29, 15.18], 'DR': [36.67, 36.14, 34.77], 'SEQ': [63.33, 63.86, 65.23], 'CR': [165.5, 171.5, 174.6], 'QR': [207.1, 215.6, 223.8], 'CURR': [239.0, 247.1, 256.7], 'ICR': [99.78, 117.1, 146.8], 'ART': [11.73, 12.99, 13.14], 'IT': [4.29, 4.68, 4.53], 'TAT': [0.42, 0.46, 0.5], 'DER': [57.89, 56.6, 53.3], 'ARD': [30.72, 27.52, 27.27], 'ITD': [84.11, 76.92, 79.65], 'OCD': [114.83, 104.44, 106.92], 'OCF': [436311108, 377668210, 391992467], 'ICF': [-159806991, -197607330, -195509921], 'FCF': [-71685617, -90244583, -83638287], 'CAPEX': [-181121318, -197901488, -198992229], 'FCFREE': [255189790, 179766722, 193000238], 'NCF': [204818500, 89816297, 112844259]})
    control_charts_reports = create_control_charts({'seasons': ['2024Q1', '2024Q2', '2024Q3'], 'GPM': [53.07, 53.17, 57.83], 'OPM': [42.02, 42.55, 47.49], 'NPM': [38.0, 36.77, 42.79], 'ROE_Q': [6.3, 6.62, 8.29], 'ROA_Q': [3.98, 4.21, 5.35], 'RGR_Q': [-5.26, 13.64, 12.8], 'TAGR_Q': [4.62, 3.36, 3.06], 'LTDR': [16.68, 16.29, 15.18], 'DR': [36.67, 36.14, 34.77], 'SEQ': [63.33, 63.86, 65.23], 'CR': [165.5, 171.5, 174.6], 'QR': [207.1, 215.6, 223.8], 'CURR': [239.0, 247.1, 256.7], 'ICR': [99.78, 117.1, 146.8], 'ART': [11.73, 12.99, 13.14], 'IT': [4.29, 4.68, 4.53], 'TAT': [0.42, 0.46, 0.5], 'DER': [57.89, 56.6, 53.3], 'ARD': [30.72, 27.52, 27.27], 'ITD': [84.11, 76.92, 79.65], 'OCD': [114.83, 104.44, 106.92], 'OCF': [436311108, 377668210, 391992467], 'ICF': [-159806991, -197607330, -195509921], 'FCF': [-71685617, -90244583, -83638287], 'CAPEX': [-181121318, -197901488, -198992229], 'FCFREE': [255189790, 179766722, 193000238], 'NCF': [204818500, 89816297, 112844259]})
    print(f'數據: {control_charts_reports}')
    
    for column_name in columns:
        plot_control_chart(control_charts_reports[column_name], column_name)
