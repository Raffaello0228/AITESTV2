import pandas as pd
import json
from typing import Dict, List, Any
import logging


def excel_to_rag_json(
    excel_path: str,
    query_col: str = "query",
    response_col: str = "answer",
    gt_answer_col: str = "gt_answer",
    context_col: str = "all_source",
) -> str:
    """
    将Excel文件转换为RAG评估所需的JSON格式

    参数:
        excel_path: Excel文件路径
        query_col: 查询列名
        response_col: 响应列名
        gt_answer_col: 标准答案列名
        context_col: 上下文列名，预期为JSON格式文本

    返回:
        JSON字符串
    """
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_path)

        results = []
        for idx, row in df.iterrows():
            if context_col in df.columns:
                context_data = json.loads(str(row[context_col]))

            # 构建单个查询结果
            result = {
                "query_id": str(idx),
                "query": str(row[query_col]),
                "response": str(row[response_col]),
                "gt_answer": str(row[gt_answer_col]),
                "retrieved_context": context_data,
            }
            results.append(result)

        # 构建最终的JSON结构
        json_data = {"results": results}
        return json.dumps(json_data, ensure_ascii=False, indent=2)

    except Exception as e:
        logging.error(f"转换Excel到JSON时发生错误: {str(e)}")
        raise
