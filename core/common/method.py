import json
from typing import Optional, Tuple
import pandas as pd
import time
import tiktoken
from core.utils.logger import logger
from dataclasses import dataclass
from functools import wraps


def export_excel_result(data, path):
    """
    增量导出测试结果到Excel文件，保持列顺序不变

    Args:
        data: 新的测试数据
        path: Excel文件路径
    """
    # 处理JSON数据
    processed_data = []
    for item in data:
        processed_item = {}
        for key, value in item.items():
            if isinstance(value, (dict, list)):
                processed_item[key] = json.dumps(value, ensure_ascii=False)
            else:
                processed_item[key] = value
        processed_data.append(processed_item)

    # 将新数据转换为DataFrame
    new_df = pd.DataFrame(processed_data)

    # 如果文件已存在，读取现有数据
    if path.exists():
        try:
            existing_df = pd.read_excel(path)

            # 使用现有DataFrame的列顺序作为基准
            base_columns = existing_df.columns.tolist()

            # 找出新DataFrame中的新列
            new_columns = [col for col in new_df.columns if col not in base_columns]

            # 将新列添加到列列表末尾
            all_columns = base_columns + new_columns

            # 为缺失的列填充空值
            for col in all_columns:
                if col not in existing_df.columns:
                    existing_df[col] = None
                if col not in new_df.columns:
                    new_df[col] = None

            # 使用确定的列顺序
            existing_df = existing_df[all_columns]
            new_df = new_df[all_columns]

            # 合并数据
            df = pd.concat([existing_df, new_df], ignore_index=True)

        except Exception as e:
            logger.warning(f"读取或处理现有Excel文件失败: {e}")
            df = new_df
    else:
        df = new_df

    # 导出到Excel
    df.to_excel(path, index=False)
    logger.info(f"测试用例结果已增量导出到: {path}")


def num_tokens_from_string(string, model="gpt-4-1106-preview"):
    """Returns the number of tokens in a text string."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(string))
    return num_tokens


def receive_stream_content(response):
    stream = response.iter_content()
    stream_content = b""
    for chunk in stream:
        stream_content += chunk
    content = stream_content.decode("UTF-8")
    return content


MAX_RETRY_COUNT = 10


def retry_if_result_none(result: Optional[Tuple[Optional[str], float]]) -> bool:
    """重试条件判断"""
    global retry_counter

    if not result or not result[0]:
        logger.warning(f"尝试重试,结果为{result}")
        retry_counter += 1
        return retry_counter < MAX_RETRY_COUNT
    retry_counter = 0
    return False


@dataclass
class AdshubPreConfig:
    """广告预处理配置类"""

    max_retries: int = 3
    retry_delay: int = 2
    default_language: str = "zh_CN"


def retry_decorator(max_retries: int = 3, delay: int = 2):
    """重试装饰器"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_count = 0
            while retry_count < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        logger.error(
                            f"{func.__name__} 失败,已重试{max_retries}次: {str(e)}"
                        )
                        raise
                    logger.warning(
                        f"{func.__name__} 失败,正在进行第{retry_count}次重试: {str(e)}"
                    )
                    time.sleep(delay * retry_count)
            return None

        return wrapper

    return decorator
