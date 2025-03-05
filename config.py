from pathlib import Path

# 测试配置
TEST_CONFIG = {
    "input_path": Path(__file__).parent
    / "tests"
    / "test_data"
    / "meetask0303测试.xlsx",
    "output_dir": Path(__file__).parent / "tests" / "test_results",
    "continue_from_last": True,
}

# 数据库配置
# DB_CONFIG = {
#     "host": "10.1.12.156",
#     "port": 3307,
#     "user": "qatest",
#     "password": "d9kHsk8rvjtwKRF04u4L",
#     "database": "ai_turing",
#     "charset": "utf8mb4",
# }


DB_CONFIG = {
    "host": "10.1.12.156",
    "port": 3307,
    "user": "ai_service",
    "password": "hw5dkxpGiQX79ugQH68f",
    "database": "ai_service",
    "charset": "utf8mb4",
}
