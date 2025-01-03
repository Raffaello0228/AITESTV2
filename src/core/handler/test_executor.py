from typing import Dict, List, Any
import pandas as pd
from pathlib import Path
from datetime import datetime


class TestResult:
    """测试结果类"""

    def __init__(self, case_id: str, api_name: str):
        self.case_id = case_id
        self.api_name = api_name
        self.request_data = None
        self.response_data = None
        self.start_time = None
        self.end_time = None
        self.status = None
        self.error = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "api_name": self.api_name,
            "request_data": self.request_data,
            "response_data": self.response_data,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": (
                (self.end_time - self.start_time).total_seconds()
                if self.start_time and self.end_time
                else None
            ),
            "status": self.status,
            "error": str(self.error) if self.error else None,
        }


class TestExecutor:

    OPERATIONS = {
        "meetask": MeetaskModel,
    }

    """测试执行器"""

    def __init__(self, api_client: Any, test_data_path: Path, result_path: Path):
        self.api_client = api_client
        self.test_data = pd.read_excel(test_data_path)
        self.result_path = result_path
        self.results: List[TestResult] = []

    def execute(self) -> None:
        """执行所有测试用例"""
        for _, case in self.test_data.iterrows():
            result = TestResult(case["case_id"], case["api_name"])
            try:
                result.start_time = datetime.now()
                result.request_data = self._prepare_request_data(case)

                # 执行API调用
                response = self._execute_api_call(case["api_name"], result.request_data)

                result.response_data = response
                result.status = "SUCCESS"

            except Exception as e:
                result.status = "FAILED"
                result.error = e
            finally:
                result.end_time = datetime.now()
                self.results.append(result)

    def _prepare_request_data(self, case: pd.Series) -> Dict[str, Any]:
        """准备请求数据"""
        return {
            key: case[key]
            for key in case.index
            if not key.startswith(("case_id", "api_name", "expected_"))
        }

    def _execute_api_call(self, api_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行API调用"""
        method = getattr(self.api_client, api_name)
        return method(data)

    def export_results(self) -> None:
        """导出测试结果"""
        results_df = pd.DataFrame([r.to_dict() for r in self.results])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_df.to_excel(
            self.result_path / f"test_results_{timestamp}.xlsx", index=False
        )
