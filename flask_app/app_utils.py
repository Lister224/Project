from analysis.control_chart import create_control_charts
import json

def handle_no():
    return {'message': '很抱歉，本系統無法支援您的要求'}

def handle_analysis(query_report): # 指標管制圖、指標預測、指標報告(若有財報，增加財報報告)
    # 處理指標數據並進行分析
    try: 
        # 去掉 "analysis:" 前綴並解析 JSON
        report_json_str = query_report[len("analysis:"):] 
        report_data = json.loads(report_json_str) 
        # 提取數據部分
        data_list = report_data.get('data', [])
        index_data = data_list[0]
        control_charts_reports = create_control_charts(index_data)

    except (ValueError, KeyError) as e: 
        return {'message': f'Error processing report: {str(e)}'},500


def handle_finvision(query_report): # 僅財報報告
    # 處理財報數據並進行分析
    try: 
        # 去掉 "finvision:" 前綴並解析 JSON
        report_json_str = query_report[len("finvision:"):] 
        report_data = json.loads(report_json_str) 
        # 提取數據部分
        data_list = report_data.get('data', [])
        for data in data_list:
            x = data
    except (ValueError, KeyError) as e: 
        return {'message': f'Error processing report: {str(e)}'},500
    financial_analysis_result = analyze_financial_report(report)
    return {'financial_analysis': financial_analysis_result}
