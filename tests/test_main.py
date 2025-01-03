import pytest
import pandas as pd
from pathlib import Path
from core.model.meetask_model import MeetaskModel
from core.handler.test_executor import TestExecutor
from core.common.test_record import TestRecord

class TestMain():
    # 创建操作函数映射
    OPERATIONS = {
        'meetask': MeetaskModel,
    }

    def get_test_cases(self, test_data, continue_from_last):
        """获取要执行的测试用例"""
        if continue_from_last:
            last_index = TestRecord.load_record()
            test_data = test_data[test_data.index >= last_index]
        return test_data.to_dict('records')

    def pytest_generate_tests(self, metafunc):
        """动态生成测试用例参数"""
        if "test_case" in metafunc.fixturenames:
            test_data = metafunc.funcargs['test_data']
            continue_from_last = metafunc.funcargs['continue_from_last']
            test_cases = self.get_test_cases(test_data, continue_from_last)
            
            if not test_cases:
                pytest.skip("没有需要执行的测试用例")
                
            metafunc.parametrize(
                "test_case",
                test_cases,
                ids=lambda x: f"case_{x['index']}"
            )

    def test_main(self, test_case):
        """参数化测试方法"""
        index = test_case['index']
        operation = test_case['operation']
        executor = self.OPERATIONS[operation]
        
        try:
            if pd.isna(test_case.get('error_type')):
                # 正常计算场景
                result = executor(**test_case)
                # assert result == test_case['expected']
            else:
                # 异常场景
                with pytest.raises(eval(test_case['error_type']), 
                               match=test_case['error_message']):
                    executor(**test_case)
        finally:
            # 保存当前执行位置
            TestRecord.save_record(index + 1)




