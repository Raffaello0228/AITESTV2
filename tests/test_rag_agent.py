import pytest
from core.event.meetask_event import meetask_question_ask
from tests.base_test_agent import BaseTestAgent


class TestRAGAgent(BaseTestAgent):
    """测试类必须以Test开头"""

    # 创建操作函数映射
    @pytest.fixture(scope="session")
    def operations(self):
        return {"meetask_question_ask": meetask_question_ask}

    def test_main(
        self, request, test_case, operations, output_path, actual_test_cases_count
    ):
        """测试方法必须以test_开头"""
        # 调用基类的test_main方法，传递实际测试用例数量
        super().test_main(
            request, test_case, operations, output_path, actual_test_cases_count
        )

    # def test_rag_evaluation(self, output_path):
    #     """
    #     在所有测试用例执行完成后执行RAG评估
    #     注意：该方法会在所有test_main执行完成后自动执行
    #     """
    #     logger.info("开始执行RAG评估...")
    #     try:
    #         from core.common.rag_checker import evaluate_rag

    #         # 确保输出文件存在
    #         if not output_path.exists():
    #             logger.warning("测试结果文件不存在，跳过RAG评估")
    #             pytest.skip("测试结果文件不存在")
    #             return

    #         # 执行RAG评估
    #         results = evaluate_rag(str(output_path), is_excel=True)

    #         # 将评估结果保存到新的Excel文件
    #         evaluation_output = (
    #             output_path.parent / f"rag_evaluation_{output_path.stem}.xlsx"
    #         )

    #         # 将评估结果转换为DataFrame并保存
    #         if results:
    #             import pandas as pd

    #             if isinstance(results, dict):
    #                 df = pd.DataFrame([results])
    #             else:
    #                 df = pd.DataFrame(results)
    #             df.to_excel(evaluation_output, index=False)
    #             logger.info(f"RAG评估结果已保存到: {evaluation_output}")

    #         return results

    #     except Exception as e:
    #         logger.error(f"RAG评估过程中发生错误: {str(e)}")
    #         raise
