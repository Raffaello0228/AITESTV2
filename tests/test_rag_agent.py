# from datetime import datetime
# import pytest
# import pandas as pd
# from pathlib import Path
# from config import TEST_CONFIG
# from core.common.method import export_excel_result
# from core.common.test_record import TestRecord
# from core.event.meetask_event import meetask_question_ask
# from core.utils.logger import logger


# def pytest_generate_tests(metafunc):
#     """动态生成测试用例"""
#     if "test_case" in metafunc.fixturenames:
#         logger.info("开始生成测试用例...")
#         # 从 config 获取测试数据
#         test_data_path = TEST_CONFIG["input_path"]
#         logger.info(f"读取测试数据: {test_data_path}")

#         df = pd.read_excel(test_data_path)
#         df = df.where(df.is_skip is pd.NA, None)
#         df = df.replace({pd.NA: None})
#         df = df.where(pd.notna(df), None)
#         df = df.reset_index()

#         logger.info(f"读取到 {len(df)} 条测试数据")

#         continue_from_last = TEST_CONFIG["continue_from_last"]
#         if continue_from_last:
#             last_index = TestRecord.load_record()
#             df = df[df.index >= last_index]

#         test_cases = df.to_dict("records")
#         if not test_cases:
#             logger.warning("没有需要执行的测试用例")
#             pytest.skip("没有需要执行的测试用例")

#         logger.info(f"生成 {len(test_cases)} 条测试用例")
#         metafunc.parametrize(
#             "test_case", test_cases, ids=lambda x: f"case_{x['index']}"
#         )


# class TestRAGAgent:
#     """测试类必须以Test开头"""

#     # 创建操作函数映射
#     OPERATIONS = {"meetask_question_ask": meetask_question_ask}

#     @pytest.fixture(scope="class")
#     def output_path(self):
#         output_dir = TEST_CONFIG["output_dir"]
#         output_dir.mkdir(parents=True, exist_ok=True)
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         return output_dir / f"test_results_{timestamp}.xlsx"

#     def test_main(self, test_case, request, output_path):
#         """测试方法必须以test_开头"""
#         if not hasattr(request.session, "export_excel"):
#             request.session.export_excel = []

#         index = test_case["index"]
#         operation = test_case["operation"]
#         clear_context = test_case["clear_context"]
#         event_func = self.OPERATIONS[operation]

#         try:
#             event_func(request, **test_case)
#         finally:
#             # 导出测试结果
#             export_excel_result(request.session.export_excel, output_path)
#             if clear_context:
#                 request.session.export_excel = []
#             # 保存当前执行位置
#             TestRecord.save_record(index + 1)

#     def test_rag_evaluation(self, output_path):
#         """
#         在所有测试用例执行完成后执行RAG评估
#         注意：该方法会在所有test_main执行完成后自动执行
#         """
#         logger.info("开始执行RAG评估...")
#         try:
#             from core.common.rag_checker import evaluate_rag

#             # 确保输出文件存在
#             if not output_path.exists():
#                 logger.warning("测试结果文件不存在，跳过RAG评估")
#                 pytest.skip("测试结果文件不存在")
#                 return

#             # 执行RAG评估
#             results = evaluate_rag(str(output_path), is_excel=True)

#             # 将评估结果保存到新的Excel文件
#             evaluation_output = (
#                 output_path.parent / f"rag_evaluation_{output_path.stem}.xlsx"
#             )

#             # 将评估结果转换为DataFrame并保存
#             if results:
#                 import pandas as pd

#                 if isinstance(results, dict):
#                     df = pd.DataFrame([results])
#                 else:
#                     df = pd.DataFrame(results)
#                 df.to_excel(evaluation_output, index=False)
#                 logger.info(f"RAG评估结果已保存到: {evaluation_output}")

#             return results

#         except Exception as e:
#             logger.error(f"RAG评估过程中发生错误: {str(e)}")
#             raise
