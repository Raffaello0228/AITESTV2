import asyncio
import logging
import os
from ragchecker import RAGResults, RAGChecker
from ragchecker.metrics import all_metrics
from typing import List, Dict, Any, Optional, Tuple
from litellm import completion
import aiofiles

from config import TEST_CONFIG
from core.common.excel_to_json import excel_to_rag_json

# 设置 Deepseek API key
os.environ["DEEPSEEK_API_KEY"] = "sk-aa65646ca63a4e1189c4bc71f24b4d26"


class CustomRAGChecker(RAGChecker):
    def __init__(self, custom_llm_func, **kwargs):
        super().__init__(**kwargs)
        self.custom_llm_func = custom_llm_func

    async def _call_llm(self, prompts: List[str], **kwargs) -> List[str]:
        """重写 _call_llm 方法以使用自定义 LLM 函数"""
        responses = []
        for prompt in prompts:
            response = await self.custom_llm_func(prompt)
            responses.append(response)
        return responses


async def deepseek_llm_function(prompt: str) -> str:
    """使用 Deepseek 模型的 LLM 函数"""
    try:
        # 将同步调用包装在 asyncio.to_thread 中
        response = await asyncio.to_thread(
            completion,
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Deepseek API 调用错误: {str(e)}")
        return None


def evaluate_rag(file_path: str, is_excel: bool = False):
    """
    评估RAG系统的性能

    参数:
        file_path: 输入文件路径 (Excel或JSON)
        is_excel: 是否为Excel文件
    """
    try:
        if is_excel:
            # 如果是Excel文件，先转换为JSON
            json_str = excel_to_rag_json(file_path)
            rag_results = RAGResults.from_json(json_str)
        else:
            # 直接读取JSON文件
            with open(file_path) as fp:
                content = fp.read()
                rag_results = RAGResults.from_json(content)

        # 初始化自定义评估器
        evaluator = CustomRAGChecker(
            custom_llm_func=deepseek_llm_function,
            batch_size_extractor=32,
            batch_size_checker=32,
            extractor_name="deepseek/deepseek-chat",
            checker_name="deepseek/deepseek-chat",
        )

        # 使用所有指标进行评估
        results = evaluator.evaluate(rag_results, all_metrics)

        # 打印评估结果
        print("评估结果:")
        print(results)

        return results

    except Exception as e:
        logging.error(f"RAG评估过程中发生错误: {str(e)}")
        raise


if __name__ == "__main__":
    evaluate_rag("tests/test_results/test_results_20250114_101852.xlsx", True)
