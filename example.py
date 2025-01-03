import logging
import os
from ragchecker import RAGResults, RAGChecker
from ragchecker.metrics import all_metrics
from typing import List, Dict, Any, Optional, Tuple
from litellm import completion



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

# 设置 Deepseek API key
os.environ['DEEPSEEK_API_KEY'] = "sk-6f03a9dd4dcf4e49950420974d9577ea"

async def deepseek_llm_function(prompt: str) -> str:
    """使用 Deepseek 模型的 LLM 函数"""
    try:
        response = completion(
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Deepseek API 调用错误: {str(e)}")
        return None

# 使用示例
with open("checking_inputs.json") as fp:
    rag_results = RAGResults.from_json(fp.read())

# 初始化自定义评估器
evaluator = CustomRAGChecker(
    custom_llm_func=deepseek_llm_function,
    batch_size_extractor=32,
    batch_size_checker=32,
    extractor_name="deepseek/deepseek-chat",
    checker_name="deepseek/deepseek-chat"
)

# 使用所有指标进行评估
evaluator.evaluate(rag_results, all_metrics)

print(rag_results)