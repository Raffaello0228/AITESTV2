from datetime import datetime
import pytest
import pandas as pd
import os
import time
from config import TEST_CONFIG
from core.common.method import export_excel_result
from core.common.test_record import TestRecord
from core.event.adshub_pre_event import adshub_pre_app, adshub_pre_eb
from core.utils.logger import logger


# 存储实际测试用例数量的全局变量
ACTUAL_TEST_CASES_COUNT = 0


def pytest_generate_tests(metafunc):
    """动态生成测试用例"""
    global ACTUAL_TEST_CASES_COUNT

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

        # 保存实际测试用例数量
        ACTUAL_TEST_CASES_COUNT = len(df)
        logger.info(f"读取到 {ACTUAL_TEST_CASES_COUNT} 条测试数据")

        continue_from_last = TEST_CONFIG["continue_from_last"]
        if continue_from_last:
            last_index = TestRecord.load_record()
            df = df[df.index >= last_index]
            logger.info(
                f"从上次执行位置 {last_index} 继续执行，剩余 {len(df)} 条测试数据"
            )
            # 更新实际需要执行的测试用例数量
            ACTUAL_TEST_CASES_COUNT = len(df)

        # 将所有测试用例转换为字典列表
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
        worker_id = os.environ.get("PYTEST_XDIST_WORKER", "")
        # 为每个worker创建单独的输出文件
        output_file = f"test_results_{timestamp}{worker_id}.xlsx"
        return output_dir / output_file

    def should_skip_test(self, test_case):
        """
        根据worker ID和测试用例索引决定是否跳过当前测试
        """
        # 获取worker信息
        worker_id = os.environ.get("PYTEST_XDIST_WORKER", None)
        total_workers = int(os.environ.get("PYTEST_XDIST_WORKER_COUNT", 1))

        # 如果不是在多worker环境中运行，或者只有一个worker，则不跳过
        if worker_id is None or total_workers <= 1:
            return False

        # 提取worker编号
        worker_index = int(worker_id[2:]) if worker_id.startswith("gw") else 0

        # 获取测试用例索引
        case_index = test_case["index"]

        # 使用更均衡的分配方式：每个worker处理连续的几个测试用例
        # 使用实际测试用例数量而不是估计值
        global ACTUAL_TEST_CASES_COUNT
        total_cases = ACTUAL_TEST_CASES_COUNT
        logger.debug(f"使用实际测试用例数量: {total_cases} 进行分配")

        cases_per_worker = total_cases // total_workers
        remainder = total_cases % total_workers

        # 计算当前worker应该处理的起始和结束索引
        start_idx = worker_index * cases_per_worker + min(worker_index, remainder)
        end_idx = start_idx + cases_per_worker + (1 if worker_index < remainder else 0)

        # 如果测试用例索引不在当前worker的范围内，则跳过
        should_skip = not (start_idx <= case_index < end_idx)

        return should_skip

    def test_main(self, test_case, request, output_path):
        """测试方法必须以test_开头"""
        # 检查是否应该跳过当前测试
        if self.should_skip_test(test_case):
            pytest.skip(f"测试用例 {test_case['index']} 不在当前worker的分配范围内")

        if not hasattr(request.session, "export_excel"):
            request.session.export_excel = []

        index = test_case["index"]
        operation = test_case["operation"]
        clear_context = test_case["clear_context"]
        event_func = self.OPERATIONS[operation]

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
        result_files = list(output_dir.glob(f"test_results_{timestamp}*.xlsx"))

        if not result_files:
            logger.warning("未找到需要合并的测试结果文件")
            return

        logger.info(f"找到 {len(result_files)} 个测试结果文件，开始合并...")

        # 合并所有Excel文件
        merged_df = pd.DataFrame()
        all_columns = set()

        # 首先收集所有可能的列
        for file_path in result_files:
            try:
                df = pd.read_excel(file_path)
                all_columns.update(df.columns)
            except Exception as e:
                logger.error(f"读取文件 {file_path} 失败: {str(e)}")

        all_columns = list(all_columns)

        # 然后合并所有文件
        for file_path in result_files:
            try:
                df = pd.read_excel(file_path)

                # 为缺失的列填充空值
                for col in all_columns:
                    if col not in df.columns:
                        df[col] = None

                # 确保列顺序一致
                df = df[all_columns]

                # 合并数据
                if merged_df.empty:
                    merged_df = df
                else:
                    merged_df = pd.concat([merged_df, df], ignore_index=True)

                logger.info(f"已合并文件: {file_path}")
            except Exception as e:
                logger.error(f"合并文件 {file_path} 失败: {str(e)}")

        if not merged_df.empty:
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
