import time
from datetime import datetime
import re
import json
import requests
import os
from requests.exceptions import ChunkedEncodingError, RequestException
from typing import Dict, Optional, Tuple, Any

from core.utils.logger import logger
from constant import AI_TURNING_URL, AI_ADSHUB_URL
from core.common.method import retry_decorator


class APIRequestError(Exception):
    """API请求异常"""

    pass


@retry_decorator(max_retries=3, delay=1)
def adshub_ask_question_stream(
    query: str,
    session_id: Optional[str] = None,
    user_id: int = 2923,
    language: str = "zh_CN",
    _agent_code: str = "PRE_AD_PLACEMENT",
) -> Dict:
    """流式问答接口"""
    url = f"{AI_TURNING_URL}/dialogue/agentStreamAskQuestion"
    data = {
        "agentCode": _agent_code,
        "agentSubType": "CHAT",
        "language": language,
        "userId": user_id,
        "userInputText": query,
    }
    if session_id:
        data.update({"conversationId": session_id})

    headers = {"accept": "*/*", "Content-Type": "application/json"}

    try:
        request_time = datetime.now()
        first_char_response_time = None
        response = requests.request(
            "POST",
            url,
            headers=headers,
            data=json.dumps(data),
            stream=True,
            timeout=180,
        )

        stream_content = b""
        for res in response.iter_content(chunk_size=1024):
            if res:
                stream_content += res
                if b"content" in stream_content and not first_char_response_time:
                    first_char_response_time = datetime.now()

        response_time = datetime.now()
        cost = (response_time - request_time).seconds if response_time else 0

        if not stream_content:
            return {
                "question": query,
                "answer": None,
                "cost": None,
                "conversation_id": None,
                "trace_id": None,
            }

        response_text = stream_content.decode("UTF-8")
        target_items = re.findall(r'(?<="content":)"[\s\S].*?"', response_text)
        content = "".join(str(x).strip().replace('"', "") for x in target_items[2:])
        answer = content.replace("\\n", "\n")
        logger.info(f"流式接受完毕:\n{content}")

        try:
            conversation_id = (
                str(re.findall(r'(?<="conversationId":)"[\s\S].*?"', response_text)[0])
                .strip()
                .replace('"', "")
            )
            trace_id = (
                str(re.findall(r'(?<="traceId":)"[\s\S].*?"', response_text)[0])
                .strip()
                .replace('"', "")
            )
        except IndexError:
            logger.error("响应体未找到conversation_id")
            conversation_id = ""
            trace_id = ""

        logger.debug(
            f"\n请求时间:{request_time}\n"
            f"首字符时间:{first_char_response_time}\n"
            f"响应时间:{cost}\n"
            f"状态码:{response.status_code}"
        )

        return {
            "question": query,
            "answer": answer,
            "cost": cost,
            "conversation_id": conversation_id,
            "trace_id": trace_id,
        }

    except (ChunkedEncodingError, RequestException) as e:
        logger.error(f"请求失败: {str(e)}")
        raise APIRequestError(f"请求失败: {str(e)}")
    except Exception as e:
        logger.error(f"未知错误: {str(e)}")
        raise


@retry_decorator(max_retries=3, delay=1)
def adshub_ad_generate_v2(data: Dict) -> Dict:
    """广告生成接口V2"""
    url = f"{AI_TURNING_URL}/preAdvertise/generatePlan"
    headers = {
        "Request-Origion": "SwaggerBootstrapUi",
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    logger.debug(json.dumps(data, ensure_ascii=False))

    try:
        response = requests.request("POST", url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()["result"]
        logger.info(f"接口返回：{result}")
        return {"result": result, "cost": response.elapsed.total_seconds()}
    except Exception as e:
        logger.error(f"请求失败: {str(e)}")
        return {"result": None, "cost": 0}


@retry_decorator(max_retries=3, delay=1)
def adshub_ad_generate(data: str) -> Tuple[Optional[Dict], float]:
    """广告生成接口"""
    url = "http://10.1.201.21:8830/ad_generate"
    headers = {
        "Request-Origion": "SwaggerBootstrapUi",
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    logger.debug(json.dumps(data, ensure_ascii=False))

    try:
        response = requests.request(
            "POST", url, headers=headers, json={"conversationId": data}
        )
        response.raise_for_status()
        result = response.json()["result"]
        logger.info(f"接口返回：{result}")
        return result, response.elapsed.total_seconds()
    except Exception as e:
        logger.error(f"请求失败: {str(e)}")
        return None, 0


# 废弃
def adshub_daily_metric_predict(data):
    url = "http://10.1.201.21:8830/daily_metric_predict"
    headers = {
        "Request-Origion": "SwaggerBootstrapUi",
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    response = requests.request("POST", url, headers=headers, json=data)
    try:
        result = response.json()["result"]
        logger.info(f"接口返回：{result}")
    except:
        result = None
        logger.info(f"接口返回：{response.status_code}")
    return result, response.elapsed.total_seconds()


def get_token() -> Optional[str]:
    """获取token"""
    try:
        with open(
            os.path.join(os.path.dirname(__file__), "../../config/token.json")
        ) as f:
            config = json.load(f)
            return config["token"]
    except Exception as e:
        logger.error(f"获取token失败: {str(e)}")
        return None


token = get_token()


@retry_decorator(max_retries=3, delay=1)
def adshub_ad_generate_backend(
    conversation_id: str,
    _agent_code: str,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
) -> Dict:
    """后端广告生成接口"""
    url = f"https://test-ai-api-gateway.meetsocial.cn/stream/sino-ai-adshub/conversation/generate"
    headers = {
        "accept": "*/*",
        "Content-Type": "application/json",
        "Agent-Code": _agent_code,
        "x-sino-jwt": token,
        "x-sino-language": "zh-CN",
    }

    if trace_id and span_id:
        headers.update(
            {
                "X-B3-TraceId": trace_id,
                "X-B3-SpanId": span_id,
                "X-B3-ParentSpanId": "8d68107ef74ced2b",
                "X-B3-Sampled": "8d68107ef74ced2b",
            }
        )

    logger.debug(json.dumps(conversation_id, ensure_ascii=False))
    payload = json.dumps({"conversationId": conversation_id})

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        result = response.json()["result"]
        logger.info(f"接口返回：{result}")
        return result
    except Exception as e:
        if response.status_code == 200:
            result = response.json()
            logger.error(f"接口返回：{result}")
            return result
        logger.error(f"接口请求失败：{response.status_code}")
        return {}


@retry_decorator(max_retries=60, delay=4)
def adshub_ad_detail_backend(
    plan_id: str,
    _agent_code: str,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
) -> Dict:
    """获取广告详情接口"""
    url = f"https://test-ai-api-gateway.meetsocial.cn/stream/sino-ai-adshub/plan/planInfo?planId={plan_id}"
    headers = {
        "accept": "*/*",
        "Content-Type": "application/json",
        "Agent-Code": _agent_code,
        "x-sino-jwt": token,
        "x-sino-language": "zh-CN",
    }

    if trace_id and span_id:
        headers.update(
            {
                "X-B3-TraceId": trace_id,
                "X-B3-SpanId": span_id,
                "X-B3-ParentSpanId": "8d68107ef74ced2b",  # 无意义,但需要传
                "X-B3-Sampled": "8d68107ef74ced2b",  # 无意义,但需要传
            }
        )
    result = None
    max_retries = 60  # 最大重试次数
    retry_count = 0
    wait_time = 4  # 初始等待时间(秒)
    status = 0
    while status == 0:
        retry_count += 1
        if retry_count >= max_retries:
            logger.warning(f"获取广告详情失败,已重试{max_retries}次")
            break

            # 指数退避等待
        response = requests.get(url, headers=headers)

        try:
            result = response.json()["result"]
            if result["planStatus"] == "SUCCESS":
                logger.info(f"接口返回：{result}")
                status = 1
            elif result["planStatus"] == "PLAN_FAIL":
                logger.error("生成方案失败")
                break
            else:
                time.sleep(wait_time)
        except:
            if response.status_code == 200:
                result = response.json()["result"]
                logger.error(f"接口返回：{result}")
            else:
                result = {}
                logger.error(f"接口请求失败：{response.status_code}")
    return result
