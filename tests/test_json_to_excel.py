import os
import json
import pandas as pd
import sys
import pytest
from pathlib import Path
from core.common.json_to_excel import json_to_excel

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).parent.parent))


@pytest.fixture
def sample_nested_json():
    return {
        "用户信息": {
            "姓名": "张三",
            "年龄": 30,
            "联系方式": {"电话": "13800138000", "邮箱": "zhangsan@example.com"},
        },
        "订单列表": [
            {
                "订单号": "ORD001",
                "商品": [
                    {"名称": "笔记本电脑", "价格": 5999, "数量": 1},
                    {"名称": "鼠标", "价格": 99, "数量": 2},
                ],
                "总价": 6197,
            },
            {
                "订单号": "ORD002",
                "商品": [{"名称": "显示器", "价格": 1299, "数量": 1}],
                "总价": 1299,
            },
        ],
    }


@pytest.fixture
def sample_list_data():
    return [
        {"id": 1, "name": "产品A", "price": 100, "tags": ["电子", "家电"]},
        {"id": 2, "name": "产品B", "price": 200, "tags": ["办公", "电子"]},
        {
            "id": 3,
            "name": "产品C",
            "price": 300,
            "tags": ["家居"],
            "details": {"color": "红色", "weight": "2kg"},
        },
    ]


@pytest.fixture
def sample_dict_with_lists():
    return {
        "店铺": "电子产品专卖店",
        "地址": {"省份": "广东", "城市": "深圳", "详细地址": "科技园区88号"},
        "产品类别": ["手机", "电脑", "配件"],
        "热销产品": [
            {"名称": "iPhone", "价格": 6999, "库存": 100},
            {"名称": "MacBook", "价格": 9999, "库存": 50},
            {"名称": "AirPods", "价格": 1299, "库存": 200},
        ],
        "促销活动": [
            {"名称": "双11大促", "折扣": 0.8, "适用产品": ["iPhone", "MacBook"]},
            {"名称": "新品上市", "折扣": 0.9, "适用产品": ["AirPods"]},
        ],
    }


# 新增测试数据
TEST_DATA = {
    "name": "测试用户",
    "age": 30,
    "skills": ["Python", "JavaScript", "SQL"],
    "address": {"city": "北京", "street": "朝阳区"},
    "projects": [{"name": "项目A", "duration": 6}, {"name": "项目B", "duration": 12}],
    "education": [
        {"degree": "学士", "school": "北京大学", "year": 2015},
        {"degree": "硕士", "school": "清华大学", "year": 2018},
    ],
}

# 嵌套复杂的测试数据
COMPLEX_TEST_DATA = {
    "results": [
        {
            "query_id": "0",
            "query": "测试问题1",
            "response": "测试回答1",
            "retrieved_context": [
                {"doc_id": "000", "text": "上下文1"},
                {"doc_id": "001", "text": "上下文2"},
            ],
            "test_data": [
                {"doc_id": "000", "text": "上下文1"},
                {"doc_id": "001", "text": "上下文2"},
                {"doc_id": "002", "text": "上下文3"},
            ],
        },
        {
            "query_id": "1",
            "query": "测试问题2",
            "response": "测试回答2",
            "retrieved_context": [{"doc_id": "002", "text": "上下文3"}],
        },
    ]
}


# def test_json_to_excel_simple():
#     """测试简单JSON数据转Excel"""
#     output_path = "output/test_simple.xlsx"

#     # 确保输出目录存在
#     os.makedirs(os.path.dirname(output_path), exist_ok=True)

#     # 调用函数
#     result_path = json_to_excel(TEST_DATA, output_path)

#     # 验证文件是否创建
#     assert os.path.exists(result_path)

#     # 读取Excel文件验证内容
#     df = pd.read_excel(result_path)
#     print("\n生成的Excel内容:")
#     print(df)

#     # 验证数据行数
#     assert len(df) > 0

#     return df


def test_json_to_excel_complex():
    """测试复杂嵌套JSON数据转Excel"""
    output_path = "output/test_complex.xlsx"

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 调用函数
    result_path = json_to_excel(COMPLEX_TEST_DATA, output_path)

    # 验证文件是否创建
    assert os.path.exists(result_path)

    # 读取Excel文件验证内容
    df = pd.read_excel(result_path)
    print("\n生成的复杂Excel内容:")
    print(df)

    # 验证数据行数
    assert len(df) > 0

    return df
