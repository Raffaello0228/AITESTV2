from copy import deepcopy
import os
import json
import pandas as pd
from typing import Dict, List, Any, Union, Optional


def is_simple(lst: List[Any]) -> bool:
    """
    判断一个列表或字典是否为简单结构(不包含嵌套的字典或列表)

    Args:
        lst: 要检查的列表或字典

    Returns:
        bool: 如果列表或字典中不包含嵌套的字典或列表则返回True,否则返回False
    """
    if isinstance(lst, dict):
        return all(not isinstance(value, (dict, list)) for value in lst.values())
    elif isinstance(lst, list):
        return all(not isinstance(item, (dict, list)) for item in lst)
    return True


def flatten_json(json_obj: Dict, parent_key: str = "", sep: str = "_") -> Dict:
    """
    将嵌套的JSON对象扁平化为单层字典

    Args:
        json_obj: 要扁平化的JSON对象
        parent_key: 父键名称，用于递归
        sep: 键名分隔符

    Returns:
        扁平化后的字典
    """
    items = {}
    for key, value in json_obj.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key

        if isinstance(value, dict):
            dict_data = flatten_json(value, new_key, sep)
            items.update(**dict_data)
        elif isinstance(value, list):
            if is_simple(value):
                list_data = {key: ",".join(str(ele) for ele in value)}
                items.update(**list_data)
            else:
                list_data = []
                for sub_items in value:
                    list_item = flatten_json(sub_items, new_key, sep)
                    list_data.append(list_item)
                items.update(**{key: list_data})
        else:
            nomal_data = {new_key: value}
            items.update(**nomal_data)
    return items


def flatten_dict_list_to_rows(handle_item: Dict, parent_item: List = None) -> str:
    """
    将字典中的列表字段转换为Excel的多行，其他字段在每行重复

    Args:
        data: 包含列表字段的字典
        output_path: 输出Excel文件路径
        list_fields: 要转换为多行的列表字段，如果为None则自动检测所有列表
        sheet_name: Excel工作表名称

    Returns:
        输出文件路径
    """
    # 扁平化非列表字段
    handle_item = handle_item
    list_data = parent_item if parent_item else []

    # 如果未指定列表字段，则自动检测
    list_fields = []
    for key, value in handle_item.items():
        if isinstance(value, list):
            list_fields.append(key)

    # 找到list_fields中最长的list
    max_list_length = 0
    for field in list_fields:
        if field in handle_item and isinstance(handle_item[field], list):
            max_list_length = max(max_list_length, len(handle_item[field]))

    # 分离列表字段和非列表字段
    for i in range(max_list_length):
        row_data = deepcopy(handle_item)
        for field in list_fields:
            if field in row_data and isinstance(row_data[field], list):
                index = list(row_data.keys()).index(field)
                items = list(row_data.items())
                try:
                    value = row_data.pop(field)
                    items.insert(index, (field, value[i]))
                except IndexError:
                    items.insert(index, (field, None))
                finally:
                    row_data = dict(items)
                if is_simple(row_data):
                    list_data.append(row_data)
                else:
                    flatten_dict_list_to_rows(row_data)
    return list_data


def flatten_dict_list_to_columns(handle_item: Dict) -> Dict:
    """
    将字典中的列表字段转换为多列，每个列表元素占用一列

    Args:
        handle_item: 包含列表字段的字典

    Returns:
        转换后的字典，列表元素被展开为多列
    """
    result = {}

    for key, value in handle_item.items():
        if isinstance(value, list):
            # 对于列表字段，创建多个列
            for i, item in enumerate(value):
                new_key = f"{key}_{i+1}"
                result[new_key] = item
        else:
            # 非列表字段保持不变
            result[key] = value

    return result


def analyze_json_structure(
    data: Union[Dict, List], parent_path: str = "", paths: set = None
) -> set:
    """
    分析JSON数据结构，获取所有可能的路径

    Args:
        data: JSON数据
        parent_path: 父路径
        paths: 已收集的路径集合

    Returns:
        所有可能路径的集合
    """
    if paths is None:
        paths = set()

    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{parent_path}.{key}" if parent_path else key
            paths.add(current_path)
            if isinstance(value, (dict, list)):
                analyze_json_structure(value, current_path, paths)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                analyze_json_structure(item, parent_path, paths)

    return paths


def json_to_tree_columns(data: Union[Dict, List]) -> pd.DataFrame:
    """
    将JSON数据转换为树状结构的DataFrame

    Args:
        data: JSON数据

    Returns:
        树状结构的DataFrame
    """

    def get_value_by_path(obj: Union[Dict, List], path: str) -> Any:
        """获取指定路径的值"""
        try:
            current = obj
            for part in path.split("."):
                if isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list):
                    # 如果是列表，返回所有元素组成的字符串
                    return ", ".join(str(x) for x in current)
                else:
                    return None
                if current is None:
                    return None
            return current if not isinstance(current, dict) else None
        except:
            return None

    # 如果是列表类型的根节点，处理每个元素
    if isinstance(data, list):
        all_rows = []
        for item in data:
            if isinstance(item, dict):
                # 获取当前元素的所有可能路径
                paths = analyze_json_structure(item)
                paths = sorted(list(paths))

                # 获取当前元素的值
                row = {path: get_value_by_path(item, path) for path in paths}
                all_rows.append(row)

        # 合并所有行的列
        all_columns = set()
        for row in all_rows:
            all_columns.update(row.keys())

        # 确保所有行都有相同的列
        for row in all_rows:
            for col in all_columns:
                if col not in row:
                    row[col] = None

        return pd.DataFrame(all_rows)

    # 如果是字典类型的根节点
    elif isinstance(data, dict):
        # 获取所有可能的路径
        paths = analyze_json_structure(data)
        paths = sorted(list(paths))

        # 创建数据行
        row = {path: get_value_by_path(data, path) for path in paths}
        return pd.DataFrame([row])


def json_to_excel(data, output_path, sheet_name="Sheet1", format_type="row"):
    """
    将JSON数据转换为Excel文件

    Args:
        data: JSON数据
        output_path: 输出Excel文件路径
        sheet_name: Excel工作表名称
        format_type: 输出格式类型，可选值：
            - "row": 按行展开（默认）
            - "column": 按列展开
            - "tree": 树状结构展开

    Returns:
        输出文件路径
    """
    if format_type == "tree":
        # 如果数据是字典且包含result字段，直接处理result
        if isinstance(data, dict) and "result" in data:
            df = json_to_tree_columns(data["result"])
        else:
            df = json_to_tree_columns(data)
    else:
        flat_data = flatten_json(data)
        if format_type == "column":
            list_data = [flatten_dict_list_to_columns(flat_data)]
        else:
            list_data = flatten_dict_list_to_rows(flat_data)
        df = pd.DataFrame(list_data)

    # 创建输出目录（如果不存在）
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    df.to_excel(output_path, sheet_name=sheet_name, index=False)
    return output_path


# 示例数据
test_data = {
    "result": [
        {
            "项目名称": "测试项目1",
            "基本信息": {
                "版本": "2.0",
                "创建时间": "2024-01-01",
                "标签": ["开发", "测试", "生产"],
            },
            "配置项": [
                {
                    "数据库": {
                        "host": "localhost",
                        "port": 3306,
                        "参数": {"超时时间": 30, "最大连接数": 100},
                    },
                    "缓存": ["Redis", "Memcached"],
                },
                {
                    "数据库": {
                        "host": "localhost",
                        "port": 3307,
                        "参数": {"超时时间": 30, "最大连接数": 100},
                    },
                    "缓存": ["Redis", "Memcached"],
                },
            ],
        },
        {
            "项目名称": "测试项目2",
            "基本信息": {
                "版本": "2.0",
                "创建时间": "2024-01-01",
                "标签": ["开发", "测试", "生产"],
            },
            "配置项": {
                "数据库": {
                    "host": "localhost",
                    "port": 3306,
                    "参数": {"超时时间": 30, "最大连接数": 100},
                },
                "缓存": ["Redis", "Memcached"],
            },
        },
    ]
}

# 使用树状结构展开
json_to_excel(test_data, "output.xlsx", format_type="tree")
