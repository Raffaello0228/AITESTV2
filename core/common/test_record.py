import json
from pathlib import Path


class TestRecord:
    """测试记录类，用于记录测试执行位置"""

    RECORD_FILE = (
        Path(__file__).parent.parent.parent
        / "tests"
        / "test_cache"
        / "test_record.json"
    )

    @classmethod
    def save_record(cls, index):
        """保存当前执行位置"""
        # 确保目录存在
        cls.RECORD_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(cls.RECORD_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_index": index}, f)

    @classmethod
    def load_record(cls):
        """加载上次执行位置"""
        try:
            with open(cls.RECORD_FILE, "r", encoding="utf-8") as f:
                return json.load(f)["last_index"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return 0

    @classmethod
    def clear_record(cls):
        """清除测试记录"""
        try:
            if cls.RECORD_FILE.exists():
                cls.RECORD_FILE.unlink()  # 删除文件
        except Exception as e:
            print(f"清除测试记录失败: {e}")
