from core.common.test_record import TestRecord
from core.utils.logger import logger
import pytest
from unittest.mock import Mock


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时的钩子函数"""
    # 清除测试记录
    TestRecord.clear_record()


def pytest_addoption(parser):
    """添加命令行参数，保持向后兼容"""
    parser.addoption("--continue-from-last", action="store_true", default=False)
    parser.addoption("--input-path", action="store", default=None)
    parser.addoption("--output-path", action="store", default=None)
