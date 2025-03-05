import pytest
from core.event.adshub_pre_event import adshub_pre_app, adshub_pre_eb
from tests.base_test_agent import BaseTestAgent


class TestChatAgent(BaseTestAgent):
    """测试类必须以Test开头"""

    @pytest.fixture(scope="session")
    def operations(self):
        return {
            "adshub_pre_eb": adshub_pre_eb,
            "adshub_pre_app": adshub_pre_app,
        }

    def test_main(
        self, request, test_case, operations, output_path, actual_test_cases_count
    ):
        """测试方法必须以test_开头"""
        # 调用基类的test_main方法，传递实际测试用例数量
        super().test_main(
            request, test_case, operations, output_path, actual_test_cases_count
        )
