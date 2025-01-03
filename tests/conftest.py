import pytest
import pandas as pd
from pathlib import Path

def pytest_configure(config):
    """测试配置钩子"""
    # 加载所有API定义
    # ApiRegistry.load_definitions()

def pytest_addoption(parser):
    """添加命令行参数"""
    parser.addoption(
        "--continue-from-last",
        action="store_true",
        default=False,
        help="从上次执行的位置继续测试"
    )

@pytest.fixture(scope="session")
def test_data(request):
    """加载测试数据的fixture"""
    test_data_path = Path(__file__).parent / "test_data" / "calculator_test_cases.xlsx"
    df = pd.read_excel(test_data_path)
    df = df.reset_index()  # 添加索引列
    return df

@pytest.fixture(scope="session")
def continue_from_last(request):
    """获取是否从上次执行位置继续的参数"""
    return request.config.getoption("--continue-from-last") 