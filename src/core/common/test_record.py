import json
from pathlib import Path

class TestRecord:
    RECORD_FILE = Path(__file__).parent / "test_data" / "last_execution.json"

    @classmethod
    def save_record(cls, index):
        """保存执行记录"""
        cls.RECORD_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(cls.RECORD_FILE, 'w', encoding='utf-8') as f:
            json.dump({"last_index": index}, f)

    @classmethod
    def load_record(cls):
        """加载上次执行记录"""
        try:
            with open(cls.RECORD_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)["last_index"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return 0 