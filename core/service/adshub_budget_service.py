import datetime
import requests
import json
from func_timeout import func_set_timeout

from core.utils import logger


@func_set_timeout(180)
def media_recommendation(data, trace_id, span_id):
    url = "http://119.23.250.96:34052/media_recommendation"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "X-B3-TraceId": trace_id,
        "X-B3-SpanId": span_id,
        "X-B3-ParentSpanId": "8d68107ef74ced2b",
        "X-B3-Sampled": "8d68107ef74ced2b",
    }
    logger.info(f"请求服务{url}:请求体:\n{json.dumps(data, ensure_ascii=False)}")
    response = requests.request("POST", url, headers=headers, json=data)
    try:
        result = response.json()["result"]
        logger.info(f"服务返回：{json.dumps(result, ensure_ascii=False)}")
    except:
        result = None
        logger.warning(f"服务异常：{response.status_code}")
    cost = response.elapsed.total_seconds()
    logger.info(f"服务耗时：{cost}")
    return result, cost


@func_set_timeout(180)
def budget_allocator(data, trace_id, span_id):
    url = "http://119.23.250.96:34052/seven_channel_budget_allocator"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "X-B3-TraceId": trace_id,
        "X-B3-SpanId": span_id,
        "X-B3-ParentSpanId": "8d68107ef74ced2b",
        "X-B3-Sampled": "8d68107ef74ced2b",
    }
    logger.info(f"请求服务{url}:请求体:\n{json.dumps(data, ensure_ascii=False)}")
    response = requests.request("POST", url, headers=headers, json=data)
    try:
        result = response.json()["result"]
        logger.info(f"服务返回：{result}")
    except:
        result = None
        logger.warning(f"服务异常：{response.status_code}")
    cost = response.elapsed.total_seconds()
    logger.info(f"服务耗时：{cost}")
    return result, cost


@func_set_timeout(180)
def media_budget_recommendation(data, trace_id, span_id):
    url = "http://119.23.250.96:34052/media_budget_recommendation"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "X-B3-TraceId": trace_id,
        "X-B3-SpanId": span_id,
        "X-B3-ParentSpanId": "8d68107ef74ced2b",
        "X-B3-Sampled": "8d68107ef74ced2b",
    }
    logger.info(f"请求服务{url}:请求体:\n{json.dumps(data, ensure_ascii=False)}")
    response = requests.request("POST", url, headers=headers, json=data)
    try:
        result = response.json()["result"]
        logger.info(f"服务返回：{result}")
    except:
        result = None
        logger.warning(f"服务异常：{response.status_code}")
    cost = response.elapsed.total_seconds()
    logger.info(f"服务耗时：{cost}")
    return result, cost
