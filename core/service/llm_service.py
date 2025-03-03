# coding:utf-8
from typing import Optional, Tuple, List, Dict, Any
import requests
from core.common.method import retry_if_result_none
from core.utils.logger import logger
from retrying import retry
from constant import OPENAI_URL

# 常量定义

API_HEADERS = {
    "Content-Type": "application/json",
    "app-id": "video_highlight",
    "app-secret": "52ym=1-iy58-mcjasdolifjux19",
}


def create_messages(
    content, system: Optional[str] = None, img_list: list[str] = None
) -> List[Dict[str, str]]:
    """创建消息格式"""
    if system:
        messages = [{"content": system, "role": "system"}]
    else:
        messages = []
    for c in content:
        if "q" in c.keys():
            messages.append({"content": c["q"], "role": "user"})
        if "a" in c.keys():
            messages.append({"content": c["a"], "role": "assistant"})
    if img_list:
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": img_url}}
                    for img_url in img_list
                ],
            }
        )
    return messages


def handle_api_response(response: requests.Response) -> Tuple[Optional[str], float]:
    """处理 API 响应"""
    try:
        result = "".join(i["message"]["content"] for i in response.json()["choices"])
        return result
    except (KeyError, IndexError) as e:
        logger.error(
            f"GPT返回结果异常\n状态码:{response.status_code}\n内容:{response.content}"
        )
        return None


# @retry(
#     retry_on_result=retry_if_result_none, stop_max_attempt_number=999, wait_fixed=6000
# )
def chat_gpt_pure_text(
    message,
    user: str = "default_user",
    model: str = "gpt-4o",
    max_tokens: int = 512,
    temperature: float = 0.0,
    top_p: float = 1.0,
) -> Tuple[Optional[str], float]:
    """
    调用 GPT-4 API 进行对话

    Args:
        question: 问题内容
        user: 用户标识
        model: 模型名称
        max_tokens: 最大token数
        temperature: 温度参数
        top_p: top_p参数
        system: 系统提示词

    Returns:
        Tuple[Optional[str], float]: (响应结果, 耗时)
    """
    data = {
        "frequency_penalty": 0,
        "max_tokens": max_tokens,
        "messages": message,
        "model": model,
        "n": 1,
        "presence_penalty": 0,
        "stop": ["##STOP##"],
        "temperature": temperature,
        "top_p": top_p,
        "user": user,
        "response_format": {"type": "json_object"},
    }

    response = requests.post(OPENAI_URL, headers=API_HEADERS, json=data)
    return handle_api_response(response)


def chat_gpt_multi_model(
    message: list,
    user: str = "default_user",
    model: str = "gpt-4o",
    max_tokens: int = 512,
    temperature: float = 0.0,
    top_p: float = 1.0,
) -> Tuple[Optional[str], float]:
    """
    多模态对话接口

    Args:
        prompt: 提示词
        img_list: 图片URL列表
        user: 用户标识
        model: 模型名称
        max_tokens: 最大token数
        temperature: 温度参数
        top_p: top_p参数

    Returns:
        Tuple[Optional[str], float]: (响应结果, 耗时)
    """

    data = {
        "frequency_penalty": 0,
        "max_tokens": max_tokens,
        "messages": create_messages(message),
        "model": model,
        "n": 1,
        "presence_penalty": 0,
        "stop": ["##STOP##"],
        "temperature": temperature,
        "top_p": top_p,
        "user": user,
    }

    response = requests.post(OPENAI_URL, headers=API_HEADERS, json=data)
    return handle_api_response(response)
