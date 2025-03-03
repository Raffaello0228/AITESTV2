from datetime import datetime
import pytest
import pandas as pd
from config import TEST_CONFIG
from core.common.method import export_excel_result
from core.common.test_record import TestRecord
from core.event.adshub_pre_event import adshub_pre_app, adshub_pre_eb
from core.utils.logger import logger


def pytest_generate_tests(metafunc):
    """动态生成测试用例"""
    if "test_case" in metafunc.fixturenames:
        logger.info("开始生成测试用例...")
        # 从 config 获取测试数据
        test_data_path = TEST_CONFIG["input_path"]
        logger.info(f"读取测试数据: {test_data_path}")

        df = pd.read_excel(test_data_path)
        df = df.where(df.is_skip.isna(), None)
        df = df.replace({pd.NA: None})
        df = df.where(pd.notna(df), None)
        df = df.reset_index()

        logger.info(f"读取到 {len(df)} 条测试数据")

        continue_from_last = TEST_CONFIG["continue_from_last"]
        if continue_from_last:
            last_index = TestRecord.load_record()
            df = df[df.index >= last_index]

        test_cases = df.to_dict("records")
        if not test_cases:
            logger.warning("没有需要执行的测试用例")
            pytest.skip("没有需要执行的测试用例")

        logger.info(f"生成 {len(test_cases)} 条测试用例")
        metafunc.parametrize(
            "test_case", test_cases, ids=lambda x: f"case_{x['index']}"
        )


class TestChatAgent:
    """测试类必须以Test开头"""

    # 创建操作函数映射
    OPERATIONS = {
        "adshub_pre_eb": adshub_pre_eb,
        "adshub_pre_app": adshub_pre_app,
    }

    @pytest.fixture(scope="class")
    def output_path(self):
        output_dir = TEST_CONFIG["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return output_dir / f"test_results_{timestamp}.xlsx"

    def test_main(self, test_case, request, output_path):
        """测试方法必须以test_开头"""
        if not hasattr(request.session, "export_excel"):
            request.session.export_excel = []

        index = test_case["index"]
        operation = test_case["operation"]
        clear_context = test_case["clear_context"]
        event_func = self.OPERATIONS[operation]

        try:
            event_func(request, **test_case)
        finally:
            # 导出测试结果
            export_excel_result(request.session.export_excel, output_path)
            if clear_context:
                request.session.export_excel = []
            # 保存当前执行位置
            TestRecord.save_record(index + 1)

    def test_rag_evaluation(self, output_path):
        pass
