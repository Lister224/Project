from fastapi import APIRouter, Request
from app.services import AppServices, DataServices
import logging

router = APIRouter()
app_service = AppServices()
data_service = DataServices()

@router.get("/")
def home():
    return {"message": "Hello, World!"}

@router.post("/query")
async def query_data(request: Request):
    logging.info('Received query request')
    input_data = await request.json()
    return app_service.handel_query(input_data)

@router.get("/results/indicator/{question_id}")
def get_indicator(question_id: int):
    return data_service.get_indicator(question_id)

@router.get("/results/cfs/{question_id}")
def get_cfs(question_id: int):
    return data_service.get_cfs(question_id)

@router.get("/results/bs/{question_id}")
def get_bs(question_id: int):
    return data_service.get_bs(question_id)

@router.get("/results/pl/{question_id}")
def get_pl(question_id: int):
    return data_service.get_pl(question_id)

@router.get("/results/control-chart/{question_id}")
def get_control_chart(question_id: int):
    return data_service.get_control_chart(question_id)

@router.get("/results/forecast/{question_id}")
def get_forecast(question_id: int):
    return data_service.get_forecast(question_id)

@router.get("/results/report/{question_id}")
def get_report(question_id: int):
    return data_service.get_report(question_id)

## 保留歷史紀錄查詢端口
# @router.get("/history_results/indicator/{question_id}")
# def get_history_indicator(question_id: int):
#     return data_service.get_history_indicator(question_id)

# @router.get("/history_results/cfs/{question_id}")
# def get_history_cfs(question_id: int):
#     return data_service.get_history_cfs(question_id)

# @router.get("/history_results/bs/{question_id}")
# def get_history_bs(question_id: int):
#     return data_service.get_history_bs(question_id)

# @router.get("/history_results/pl/{question_id}")
# def get_history_pl(question_id: int):
#     return data_service.get_history_pl(question_id)

# @router.get("/history_results/control-chart/{question_id}")
# def get_history_control_chart(question_id: int):
#     return data_service.get_history_control_chart(question_id)

# @router.get("/history_results/forecast/{question_id}")
# def get_history_forecast(question_id: int):
#     return data_service.get_history_forecast(question_id)

# @router.get("/history_results/report/{question_id}")
# def get_history_report(question_id: int):
#     return data_service.get_history_report(question_id)