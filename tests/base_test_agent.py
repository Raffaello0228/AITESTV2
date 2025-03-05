from datetime import datetime
import pytest
import pandas as pd
import os
import time
from config import TEST_CONFIG
from core.common.method import export_excel_result
from core.common.test_record import TestRecord
from core.utils.logger import logger
from tests.conftest import get_actual_test_cases_count, get_last_test_index


class BaseTestAgent:
    """
    测试基类，提供通用的测试功能
    子类需要定义OPERATIONS字典，映射操作名称到对应的函数
    """

    # 子类需要重写此字典，映射操作名称到函数
    @pytest.fixture(scope="session")
    def operations(self):
        return {}

    @pytest.fixture(scope="class")
    def output_path(self):
        """生成输出文件路径"""
        output_dir = TEST_CONFIG["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        worker_id = os.environ.get("PYTEST_XDIST_WORKER", "")
        # 为每个worker创建单独的输出文件
        output_file = f"test_results_{timestamp}{worker_id}.xlsx"
        return output_dir / output_file

    @pytest.fixture(scope="session")
    def actual_test_cases_count(self):
        return get_actual_test_cases_count()

    def should_skip_test(self, test_case, actual_test_cases_count):
        """
        判断当前worker是否应该跳过当前测试用例

        Args:
            test_case: 当前测试用例
            actual_test_cases_count: 实际测试用例数量

        Returns:
            bool: 是否应该跳过
        """
        # 获取当前worker ID和总worker数
        worker_id = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
        if worker_id == "主进程":
            worker_id = "gw0"

        # 从worker ID中提取数字部分
        worker_num = int(worker_id[2:]) if worker_id.startswith("gw") else 0
        total_workers = int(os.environ.get("PYTEST_XDIST_WORKER_COUNT", "1"))

        # 获取测试用例索引
        case_index = test_case["index"]

        # 计算当前worker应该处理的测试用例范围
        cases_per_worker = actual_test_cases_count // total_workers
        remainder = actual_test_cases_count % total_workers

        # 计算当前worker的起始和结束索引
        start_idx = worker_num * cases_per_worker + min(worker_num, remainder)
        end_idx = start_idx + cases_per_worker + (1 if worker_num < remainder else 0)

        # 判断当前测试用例是否在当前worker的处理范围内
        should_skip = not (start_idx <= case_index < end_idx)

        return should_skip

    def test_main(
        self, request, test_case, operations, output_path, actual_test_cases_count
    ):
        """
        主测试方法，子类可以直接使用或重写

        Args:
            test_case: 当前测试用例
            request: pytest请求对象
            output_path: 输出文件路径
            actual_test_cases_count: 实际测试用例数量
        """
        # 检查是否应该跳过当前测试
        if self.should_skip_test(test_case, actual_test_cases_count):
            pytest.skip(f"测试用例 {test_case['index']} 不在当前worker的分配范围内")

        if not hasattr(request.session, "export_excel"):
            request.session.export_excel = []

        index = test_case["index"]
        operation = test_case["operation"]
        clear_context = test_case["clear_context"]

        # 检查操作是否在OPERATIONS字典中
        if operation not in operations:
            raise ValueError(f"未定义的操作: {operation}，请在子类中定义OPERATIONS字典")

        event_func = operations[operation]

        worker_id = os.environ.get("PYTEST_XDIST_WORKER", "主进程")
        logger.info(f"Worker {worker_id} 开始执行测试用例 {index}")

        start_time = time.time()
        try:
            event_func(request, **test_case)
            elapsed_time = time.time() - start_time
            logger.info(
                f"Worker {worker_id} 完成测试用例 {index}，耗时 {elapsed_time:.2f} 秒"
            )
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                f"Worker {worker_id} 执行测试用例 {index} 失败，耗时 {elapsed_time:.2f} 秒，错误: {str(e)}"
            )
            raise
        finally:
            # 导出测试结果
            export_excel_result(request.session.export_excel, output_path)
            if clear_context:
                request.session.export_excel = []
            # 保存当前执行位置
            TestRecord.save_record(index + 1)

    @pytest.fixture(scope="class")
    def merge_excel(self):
        """
        在所有测试完成后，合并所有worker生成的Excel结果文件
        """
        # 使用yield让测试先执行
        yield

        # 测试完成后执行合并操作
        output_dir = TEST_CONFIG["output_dir"]
        timestamp = datetime.now().strftime("%Y%m%d")

        # 查找当天生成的所有测试结果文件
        result_files = sorted(
            output_dir.glob(f"test_results_{timestamp}*.xlsx"),
            key=lambda x: x.stat().st_mtime,
        )

        if not result_files:
            logger.warning("未找到需要合并的测试结果文件")
            return

        logger.info(f"找到 {len(result_files)} 个测试结果文件，开始合并...")

        # 只读取一次文件
        dataframes = []
        all_columns = set()

        for file_path in result_files:
            try:
                df = pd.read_excel(file_path)
                dataframes.append(df)
                all_columns.update(df.columns)
                logger.info(f"已读取文件: {file_path}")
            except Exception as e:
                logger.error(f"读取文件 {file_path} 失败: {str(e)}")

        # 如果没有成功读取任何文件，直接返回
        if not dataframes:
            logger.warning("没有成功读取任何文件，合并操作取消")
            return

        # 一次性合并所有DataFrame
        all_columns = list(all_columns)
        merged_df = pd.concat(
            [df.reindex(columns=all_columns) for df in dataframes], ignore_index=True
        )

        # 生成合并后的文件名
        merged_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        merged_file = output_dir / f"merged_results_{merged_timestamp}.xlsx"

        # 导出合并后的结果
        merged_df.to_excel(merged_file, index=False)
        logger.info(f"所有测试结果已合并到: {merged_file}")

        # 可选：删除或归档原始文件
        # for file_path in result_files:
        #     try:
        #         # 创建归档目录
        #         archive_dir = output_dir / "archived"
        #         archive_dir.mkdir(exist_ok=True)
        #         # 移动到归档目录
        #         shutil.move(str(file_path), str(archive_dir / file_path.name))
        #         logger.info(f"已归档原始文件: {file_path}")
        #     except Exception as e:
        #         logger.error(f"归档文件 {file_path} 失败: {str(e)}")
