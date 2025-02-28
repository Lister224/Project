from fastapi import HTTPException
from app.app_utils import AppUtils
from pymongo import MongoClient
from dotenv import load_dotenv
import multiprocessing
import os
import logging

class AppServices:
    def __init__(self):
        # 初始化 MongoDB 連接
        load_dotenv()
        MONGO_URI = os.environ.get("mongo_uri")
        client = MongoClient(MONGO_URI)
        self.db = client["Finvision"]
        self.utils = AppUtils()
        # 用於存儲臨時查詢結果的字典
        self.user_inputs = {}
        self.finvision_data = {}
        self.indicator_data = {}
        self.llm_reports = {}
        self.analysis_results = {}

        # 檢查question_id存在
        self.utils.init_question_id()

    # 使用者輸入問題
    def handel_query(self, input_data):
        logging.info("Received query request")

        # 如果是模糊搜尋請求
        if any("keyWord" in row for row in input_data["rows"]):
            suggestions = self.utils.handle_fuzzy_search(input_data)
            response = {
                    "status": "success",
                    "msg": "查詢成功",
                    "keyWord":suggestions
                }
            return response

        # 如果是完整查詢請求
        if input_data:
            question_id, query_report = self.utils.handle_full_query(input_data, self.user_inputs, 
                                                          self.finvision_data, self.indicator_data, 
                                                          self.llm_reports)
            
            # 判斷是否不為系統支援問題
            if question_id in ["no", "LLM_error", "error_search", "system_error"]:
                
                return {
                    "status": "ng",
                    "rows": [],
                    "msg": "很抱歉，本系統不支援您的問題!" if question_id == "no" else 
                        "很抱歉，LLM連線異常，請稍後再試!" if question_id == "LLM_error" else
                        "很抱歉，本系統資料庫沒有您要查詢的數據!" if question_id == "error_search" else
                        "很抱歉，本系統異常，請稍後再試!"
                    }

            # 多進程執行數據分析、永久儲存
            process = multiprocessing.Process(target=self.utils.background_processing, 
                                            args=(question_id, query_report,
                                                self.analysis_results,self.llm_reports ,self.finvision_data, 
                                                self.indicator_data, self.user_inputs))
            process.start()
                
            # 主執行返回結果
            response = {
                "status": "ok",
                "rows": [
                    {
                        "questionId": question_id,
                        "questionDate":self.user_inputs[question_id]["question_date"],
                        "questionTime":self.user_inputs[question_id]["question_time"],
                        "questionContent": self.user_inputs[question_id]["user_input"]
                    }
                ],
                "msg": "處理成功"
            }
            print(f"GET questionId: {question_id}")
            logging.info("Query handled successfully")
            return response
        
        else:
            response = {"status": "ng", 
                "rows": [], 
                "msg": "處理失敗" }
            logging.info("Failed to handle query")
            return response

class DataServices(AppServices):
    def __init__(self):
        super().__init__()

    # 取得常見資料
    def get_common_response_fields(self, question_id: int):
        return {
            "questionId": question_id,
            "AnswerId": self.user_inputs[question_id]["answer_id"],
            "questionDate": self.user_inputs[question_id]["question_date"],
            "questionTime": self.user_inputs[question_id]["question_time"],
            "answerDate": self.user_inputs[question_id]["answer_date"],
            "answerTime": self.user_inputs[question_id]["answer_time"],
        }
    
    # 取得指標查詢資料
    def get_indicator(self,question_id: int):
        index_data = self.indicator_data.get(question_id)
        if index_data:
            response = {
                "status": "ok",
                "rows": [
                    {
                    **self.get_common_response_fields(question_id),
                    "IndicatorContent": self.indicator_data
                    }
                ],
                "msg": "查詢成功"
            }
            return response
        else:
            return self.get_history_indicator(question_id)

    # 取得現金流量表查詢資料
    def get_cfs(self, question_id:int):
        cfs_data = self.finvision_data.get(question_id, [])[0] if self.finvision_data.get(question_id) else None  # 第一個list
        if cfs_data:
            # 將現有的 CFS 內容封裝到前端要求的格式中
            response = {
                "status": "ok",
                "rows": [
                    {
                    **self.get_common_response_fields(question_id),
                    "CFSContent": cfs_data  # 將 CFS 內容封裝到 CFSContent 中
                    }
                ],
                "msg": "查詢成功"
            }
            return response

        else: 
            return self.get_history_cfs(question_id)

    # 取得資產負債表查詢資料
    def get_bs(self, question_id):
        bs_data = self.finvision_data.get(question_id, [])[1] if self.finvision_data.get(question_id) else None  # 第二個list
        if bs_data:
            # 將現有的 BS 內容封裝到前端要求的格式中
            response = {
                "status": "ok",
                "rows": [
                    {
                    **self.get_common_response_fields(question_id),
                    "BSContent": bs_data  # 將 bS 內容封裝到 BSContent 中
                    }
                ],
                "msg": "查詢成功"
            }
            return response

        else: 
            return self.get_history_bs(question_id)
        
    # 取得損益表查詢資料
    def get_pl(self, question_id):
        pl_data = self.finvision_data.get(question_id, [])[2] if self.finvision_data.get(question_id) else None  # 第三個list
        if pl_data:
            # 將現有的 PL 內容封裝到前端要求的格式中
            response = {
                "status": "ok",
                "rows": [
                    {
                    **self.get_common_response_fields(question_id),
                    "PLContent": pl_data  # 將 pl 內容封裝到 PLContent 中
                    }
                ],
                "msg": "查詢成功"
            }
            return response

        else: 
            return self.get_history_pl(question_id)

    # 取得分析報告數據
    def get_report(self, question_id): 
        # 先從 `llm_reports` 取值
        if question_id in self.llm_reports:
            report = self.llm_reports[question_id]
            if report == "error":
                response = {"status": "ng", "rows": [], "msg": "LLM 分析報告生成異常!"}
            else:
                response = {
                    "status": "ok",
                    "rows": [
                        {
                        **self.get_common_response_fields(question_id),
                        "answerContent": report # 將 report 內容封裝到 answerContent 中
                        }
                    ],
                    "msg": "查詢成功"
                }
        # 若無再從 MongoDB 取值    
        else: 
            return self.get_history_llm_report(question_id)

        return response

    # 取得管制圖點位數據
    def get_control_chart(self, question_id):
        control_chart = self.analysis_results.get(question_id, {}).get("control_chart") 
        if control_chart == "error":
                response = {"status": "ng", 
                "rows": [], 
                "msg": "No control_chart data found for the given question_id" }
        elif control_chart:
            response = {
                "status": "ok",
                "rows": [
                    {
                    **self.get_common_response_fields(question_id),
                    "plotContent": control_chart  # 將 control_chart 內容封裝到 plotContent 中
                    }
                ],
                "msg": "查詢成功"
            }
        else: # 暫存無資料，從歷史紀錄取得
            return self.get_history_control_chart(question_id)
        
        return response

    # 取得預測點位數據
    def get_forecast(self, question_id): 
        forecast = self.analysis_results.get(question_id, {}).get("forecast") 
        if forecast == "error":
            response = {"status": "ng", 
                "rows": [], 
                "msg": "No forecast data found for the given question_id"}
        elif forecast:
            response = {
                "status": "ok",
                "rows": [               
                    {
                    **self.get_common_response_fields(question_id),
                    "forecastContent": forecast # 將 forecast 內容封裝到 forecastContent 中
                    }
                ],
                "msg": "查詢成功"
            }
        else: # 暫存無資料，從歷史紀錄取得
            return self.get_history_forecast(question_id)
        return response

    ### 歷史資料(永久儲存)
    # 取得歷史常見資料
    # 取得歷史常見資料
    def get_history_common_response_fields(self, question_id: int):
        # 使用者提問資料
        collection_common = self.db["user_inputs"]
        # 查找資料，根據 question_id 相等
        user_inputs_history = collection_common.find_one(
            {"question_id": question_id})

        logging.debug(f"MongoDB query result for question_id {question_id}: {user_inputs_history}")

        if user_inputs_history is None:
            logging.error(f"No data found in MongoDB for question_id {question_id}")
            return {}  # 或者引发异常，具体取决于你的需求
        
        try:
            return {
                "questionId": question_id,
                "AnswerId": user_inputs_history["answer_id"],  # 直接使用 "answer_id"
                "questionDate": user_inputs_history["question_date"], # 直接使用 "question_date"
                "questionTime": user_inputs_history["question_time"], # 直接使用 "question_time"
                "answerDate": user_inputs_history["answer_date"],   # 直接使用 "answer_date"
                "answerTime": user_inputs_history["answer_time"],   # 直接使用 "answer_time"
            }
        except KeyError as e:
            logging.error(f"KeyError accessing user_inputs_history: {e}")
            return {}  # 或者引发异常

    # 取得指標歷史紀錄
    def get_history_indicator(self, question_id):
        # 指標資料
        collection_2 = self.db["indicator_data"] 
        history_indicator_data = collection_2.find_one(
            {"question_id": question_id},
            {"data": 1, "_id": 0})
        
        history_indicator = history_indicator_data["data"] if history_indicator_data else {}
        if history_indicator:
            response = {
                "status": "ok",
                "rows": [
                    {
                    **self.get_history_common_response_fields(question_id),
                    "IndicatorContent": history_indicator
                    }
                ],
                "msg": "查詢成功"
            }
        else:
            response = {
                "status": "ng",
                "rows": [],
                "msg": "No Indicator data found for the given question_id"
            }
        return response

    # 取得cfs歷史紀錄
    def get_history_cfs(self, question_id):

        # 指標資料
        collection_2 = self.db["finvision_data"] 
        # 查找資料，根據 question_id 相等
        history_cfs_data = collection_2.find_one(
            {"question_id": question_id},
            {"data": 1, "_id": 0})
        
        history_cfs = history_cfs_data["data"][0] if history_cfs_data else {}
        if history_cfs:
            response = {
                "status": "ok",
                "rows": [
                    {
                    **self.get_history_common_response_fields(question_id),
                    "CFSContent": history_cfs
                    }
                ],
                "msg": "查詢成功"
            }
        else:
            response = {
                "status": "ng",
                "rows": [],
                "msg": "No CFS data found for the given question_id"
            }
        return response

    # 取得bs歷史紀錄
    def get_history_bs(self, question_id):

        # 指標資料
        collection_2 = self.db["finvision_data"] 

        # 查找資料，根據 question_id 相等
        history_bs_data = collection_2.find_one(
            {"question_id": question_id},
            {"data": 1, "_id": 0})
        
        history_bs = history_bs_data["data"][1] if history_bs_data else {}
        if history_bs:
            response = {
                "status": "ok",
                "rows": [
                    {
                    **self.get_history_common_response_fields(question_id),
                    "BSContent": history_bs
                    }
                ],
                "msg": "查詢成功"
            }
        else:
            response = {
                "status": "ng",
                "rows": [],
                "msg": "No BS data found for the given question_id"
            }
        return response

    # 取得pl歷史紀錄
    def get_history_pl(self, question_id):
        # 指標資料
        collection_2 = self.analysis_resultsdb["finvision_data"] 

        # 查找資料，根據 question_id 相等
        history_pl_data = collection_2.find_one(
            {"question_id": question_id},
            {"data": 1, "_id": 0})
        
        history_pl = history_pl_data["data"][2] if history_pl_data else {}
        if history_pl:
            response = {
                "status": "ok",
                "rows": [
                    {
                    **self.get_history_common_response_fields(question_id),
                    "PLContent": history_pl
                    }
                ],
                "msg": "查詢成功"
            }
        else:
            response = {
                "status": "ng",
                "rows": [],
                "msg": "No PL data found for the given question_id"
            }
        return response

    # 取得control_chart歷史紀錄
    def get_history_control_chart(self, question_id):
        # 指標資料
        collection_2 = self.db["analysis_results"] 

        # 查找資料，根據 question_id 相等
        history_control_chart_data = collection_2.find_one(
            {"question_id": question_id})
        
        history_control_chart = history_control_chart_data["data"]["control_chart"] if history_control_chart_data else {}
        # 當時無資料或生成失敗
        if history_control_chart == "error":
                response = {"status": "ng", 
                "rows": [], 
                "msg": "No control_chart data found for the given question_id" }
        # 當時有資料  
        elif history_control_chart:
            response = {
                "status": "ok",
                "rows": [
                    {
                    **self.get_history_common_response_fields(question_id),
                    "plotContent": history_control_chart
                    }
                ],
                "msg": "查詢成功"
            }
        # 無紀錄，現在生成中
        else:
            response = {
                "status": "pending",
                "rows": [],
                "msg": "管制圖尚在產生中!"
            }
        return response

    # 取得forecast歷史紀錄
    def get_history_forecast(self, question_id):
        # 指標資料
        collection_2 = self.db["analysis_results"] 

        # 查找資料，根據 question_id 相等
        history_forecast_data = collection_2.find_one(
            {"question_id": question_id})
        
        history_forecast = history_forecast_data["data"]["forecast"] if history_forecast_data else {}
        # 當時無資料或生成失敗
        if history_forecast == "error":
            response = {"status": "ng", 
                "rows": [], 
                "msg": "No forecast data found for the given question_id"}
        # 當時有資料
        elif history_forecast:
            response = {
                "status": "ok",
                "rows": [
                    {
                    **self.get_history_common_response_fields(question_id),
                    "forecastContent": history_forecast
                    }
                ],
                "msg": "查詢成功"
            }
        # 無紀錄，現在生成中
        else:
            response = {
                "status": "pending",
                "rows": [],
                "msg": "指標預測尚在產生中!"
            }
        return response

    # 取得llm_report歷史紀錄
    def get_history_llm_report(self, question_id):
        # 指標資料
        collection_2 = self.db["analysis_results"] 

        # 查找資料，根據 question_id 相等
        history_llm_report_data = collection_2.find_one(
            {"question_id": question_id})
        
        history_llm_report = history_llm_report_data["data"]["llm_report"] if history_llm_report_data else {}
        # 當時無資料或生成失敗
        if history_llm_report == "error":
            response = {"status": "ng", 
            "rows": [], 
            "msg": "LLM分析報告生成異常!"}
        # 當時有資料
        elif history_llm_report:
            response = {
                "status": "ok",
                "rows": [
                    {
                    **self.get_history_common_response_fields(question_id),
                    "answerContent": history_llm_report
                    }
                ],
                "msg": "查詢成功"
            }
        # 無紀錄，現在生成中
        else:
            response = {
                "status": "pending",
                "rows": [],
                "msg": "LLM分析報告尚在生成中!"
            }
        return response
