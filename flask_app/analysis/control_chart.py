import pandas as pd
import pymysql


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
            

# 取db資料
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
    db = Database(host='127.0.0.1', 
                  user='root', 
                  password='el89829603', 
                  database='finvision')
    db.connect()
    result = db.execute_query(sql_query)
    db.close()
    return(result)

# 獲取指標名
def get_column_name(index_data):
    if isinstance(index_data, list) and len(index_data) > 0:
        # 從第一個字典中獲取所有 key
        data_dict = index_data[0]
        # 使用列表推導式來過濾 key
        keys = [key for key in data_dict.keys() if key != 'seasons']
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
    
    return all_charts

#  繪製管制圖
def plot_control_chart(charts_data): 
    """ 為所有欄位繪製管制圖並直接顯示 Args: 
    charts_data (dict): 包含所有欄位管制圖數據的字典 
    """ 
    import matplotlib.pyplot as plt 
    # 計算需要的子圖數量 
    n_charts = len(charts_data) 
    # 創建圖表和子圖 
    fig, axs = plt.subplots(n_charts, 1, figsize=(12, 5*n_charts)) 
    if n_charts == 1: 
        axs = [axs] 
    # 設置子圖之間的間距 
    plt.subplots_adjust(hspace=0.4) 
    for idx, (column_name, chart_data) in enumerate(charts_data.items()): 
        # 將數據轉換回 DataFrame
        df = pd.DataFrame(chart_data) 
        # 獲取當前子圖 
        ax = axs[idx] 
        # 繪製原始數據和 EMA 
        ax.plot(df['seasons'], df[column_name], 'k.-', label='Raw Data') 
        ax.plot(df['seasons'], df['ema'], 'm--', label='EMA') 
        # 繪製控制限 
        # # 使用不同顏色的控制線 
        control_limits = [ {'sigma': 3, 'color': 'red', 'style': '-'}, 
                        {'sigma': 2, 'color': 'orange', 'style': ':'}, 
                        {'sigma': 1, 'color': 'green', 'style': ':'} ] 
        for limit in control_limits: 
            sigma = limit['sigma'] 
            color = limit['color'] 
            style = limit['style'] 
            
            # 繪製上下限 
            ax.plot(df['seasons'], df[f'UCL_{sigma}sigma'], 
                    color=color, linestyle=style, label=f'+{sigma}σ') 
            ax.plot(df['seasons'], df[f'LCL_{sigma}sigma'], 
                    color=color, linestyle=style, label=f'-{sigma}σ') 
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
   control_charts_reports = create_control_charts([{"seasons": "202403", "tagr_q": 34264319}])
   print(f'數據:{control_charts_reports}')
   plot_control_chart(control_charts_reports)
