from pathlib import Path

# 测试配置
TEST_CONFIG = {
    "input_path": Path(__file__).parent / "tests" / "test_data" / "行业分类测试集.xlsx",
    "output_dir": Path(__file__).parent / "tests" / "test_results",
    "continue_from_last": True,
}

# 数据库配置
DB_CONFIG = {
    "host": "10.1.12.156",
    "port": 3307,
    "user": "qatest",
    "password": "d9kHsk8rvjtwKRF04u4L",
    "database": "ai_turing",
    "charset": "utf8mb4",
}
