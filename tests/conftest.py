from core.common.test_record import TestRecord
from core.utils.logger import logger
import pytest
import pandas as pd
import numpy as np
from config import TEST_CONFIG
import os
import sys
import time
from pathlib import Path
import filelock
import tempfile


# 全局变量，用于存储实际测试用例数量
ACTUAL_TEST_CASES_COUNT = 0
# 全局变量，用于存储上次执行位置
LAST_TEST_INDEX = 0
# 全局变量，用于存储测试用例
TEST_CASES = []
# 文件锁路径
LOCK_FILE = Path(tempfile.gettempdir()) / "pytest_test_cases.lock"


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时的钩子函数"""
    # 清除测试记录
    TestRecord.clear_record()


def pytest_generate_tests(metafunc):
    """生成测试用例"""
    if "test_case" in metafunc.fixturenames:
        global ACTUAL_TEST_CASES_COUNT, LAST_TEST_INDEX, TEST_CASES

        # 检查是否已经读取过测试数据
        if not TEST_CASES:
            logger.info("开始生成测试用例...")

            # 使用文件锁确保只有一个进程初始化测试用例
            lock = filelock.FileLock(LOCK_FILE)
            try:
                with lock.acquire(timeout=60):  # 设置超时时间为60秒
                    # 再次检查是否已经读取过测试数据（可能在等待锁的过程中被其他进程初始化）
                    if not TEST_CASES:
                        # 读取测试数据
                        test_data_path = TEST_CONFIG["input_path"]
                        logger.info(f"读取测试数据: {test_data_path}")

                        try:
                            df = pd.read_excel(test_data_path)
                            # 重置索引
                            df = df.reset_index()

                            # 处理is_skip列
                            if "is_skip" in df.columns:
                                df = df[df.is_skip.isna() | (df.is_skip != 1)]

                            # 保存实际测试用例数量
                            ACTUAL_TEST_CASES_COUNT = len(df)
                            logger.info(f"读取到 {ACTUAL_TEST_CASES_COUNT} 条测试数据")

                            # 获取上次执行位置
                            continue_from_last = TEST_CONFIG["continue_from_last"]
                            LAST_TEST_INDEX = 0
                            if continue_from_last:
                                LAST_TEST_INDEX = TestRecord.load_record()
                                logger.info(
                                    f"上次执行位置: {LAST_TEST_INDEX}，总测试数据: {len(df)} 条"
                                )
                                # 过滤数据
                                df = df[df.index >= LAST_TEST_INDEX]
                                logger.info(
                                    f"从上次执行位置 {LAST_TEST_INDEX} 继续执行，剩余 {len(df)} 条测试数据"
                                )

                            # 将所有测试用例转换为字典列表，确保NaN值被转换为None
                            df = df.replace({np.nan: None})
                            TEST_CASES = df.to_dict("records")

                            logger.info(f"测试用例初始化完成，共 {len(TEST_CASES)} 条")
                        except Exception as e:
                            logger.error(f"生成测试用例失败: {str(e)}")
                            raise
            except filelock.Timeout:
                logger.warning("等待获取文件锁超时，可能其他进程正在初始化测试用例")
                # 等待一段时间，希望其他进程能够完成初始化
                time.sleep(5)
                # 如果TEST_CASES仍然为空，则可能是其他进程初始化失败
                if not TEST_CASES:
                    logger.error("测试用例初始化失败")
                    pytest.skip("测试用例初始化失败")

        # 所有worker都已经读取了相同的数据
        if not TEST_CASES:
            logger.warning("没有需要执行的测试用例")
            pytest.skip("没有需要执行的测试用例")

        logger.info(f"生成 {len(TEST_CASES)} 条测试用例")
        metafunc.parametrize(
            "test_case", TEST_CASES, ids=lambda x: f"case_{x['index']}"
        )


def get_actual_test_cases_count():
    """获取实际测试用例数量的函数，供测试文件使用"""
    global ACTUAL_TEST_CASES_COUNT
    return ACTUAL_TEST_CASES_COUNT


def get_last_test_index():
    """获取上次执行的测试索引，供should_skip_test使用"""
    global LAST_TEST_INDEX
    return LAST_TEST_INDEX
