# RAG 评估工具

这是一个用于评估检索增强生成(RAG)系统性能的自动化测试工具。该工具支持批量测试用例执行，并能够自动生成详细的评估报告。

## 功能特点

- 支持 Excel 格式的测试用例批量导入
- 自动化测试执行与结果记录
- RAG 系统性能评估
- 详细的评估指标分析
- 支持测试结果导出为 Excel
- 完整的日志记录系统
- 断点续测功能

## 项目结构

    project/
    ├── config.py # 配置文件
    ├── settings.py # 系统设置
    ├── core/
    │ ├── common/
    │ │ ├── excel_to_json.py # Excel转JSON工具
    │ │ ├── method.py # 通用方法
    │ │ ├── rag_checker.py # RAG评估核心
    │ │ └── test_record.py # 测试记录管理
    │ ├── event/
    │ │ └── meetask_event.py # 事件处理
    │ ├── model/
    │ │ └── meetask_model.py # 数据模型
    │ ├── service/
    │ │ └── meetask_service.py # 业务服务
    │ └── utils/
    │ └── logger.py # 日志工具
    └── tests/
    └── test_general_rag.py # RAG测试

## 安装说明

1. 克隆项目

    git clone [repository_url]
    cd [project_name]

2. 安装依赖

    pip install -r requirements.txt

3. 配置环境

- 复制 `config.example.py` 为 `config.py`
- 设置必要的环境变量和配置项

## 使用方法

1. 准备测试数据

- 按照模板格式准备 Excel 测试用例文件
- 将测试文件放置在指定目录

2. 运行测试

    pytest tests/test_general.py -v

3. 查看结果

- 测试结果将保存在配置的输出目录中
- RAG 评估报告将自动生成

## 配置说明

### 主要配置项

    TEST_CONFIG = {
    "input_path": "path/to/test/cases.xlsx", # 测试用例文件路径
    "output_dir": "path/to/output", # 输出目录
    "continue_from_last": True, # 是否从上次中断处继续
    }

### API 配置

    os.environ["DEEPSEEK_API_KEY"] = "your-api-key" # DeepSeek API密钥

## 测试用例格式

Excel 测试用例文件需包含以下字段：

- operation: 操作类型
- query: 测试问题
- expected_result: 预期结果
- clear_context: 是否清除上下文

## 评估指标

工具包含多个评估指标：

- 响应准确性
- 检索相关性
- 答案完整性
- 响应时间
- 资源利用率

## 注意事项

1. 确保所有依赖包都已正确安装
2. 测试前检查配置文件的正确性
3. 大规模测试建议启用断点续测功能
4. 定期备份测试结果数据

## 常见问题

1. Q: 如何处理测试中断？
   A: 设置 `continue_from_last=True` 可从上次中断处继续

2. Q: 如何自定义评估指标？
   A: 在 `core/common/rag_checker.py` 中添加新的评估方法

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 许可证

[许可证类型]

## 联系方式

[联系信息]

## JSON到Excel转换功能

本项目提供了将JSON数据转换为Excel文件的功能，支持多种转换方式。

### 主要功能

1. **基本JSON转Excel**：将JSON数据转换为Excel文件，支持扁平化嵌套结构。
   ```python
   from core.common.json_to_excel import json_to_excel
   
   # 扁平化转换
   json_to_excel(json_data, "output.xlsx")
   
   # 不扁平化转换
   json_to_excel(json_data, "output.xlsx", flatten=False)
   ```

2. **列表转Excel**：将JSON中的列表转换为Excel中的多行数据。
   ```python
   from core.common.json_to_excel import list_to_excel
   
   # 直接转换列表
   list_to_excel(list_data, "output.xlsx")
   
   # 从字典中提取列表
   list_to_excel(json_data, "output.xlsx", list_key="列表字段名")
   ```

3. **列表字段转多行**：将字典中的列表字段转换为Excel的多行，其他字段在每行重复。
   ```python
   from core.common.json_to_excel import flatten_dict_list_to_rows
   
   # 自动检测所有列表字段
   flatten_dict_list_to_rows(json_data, "output.xlsx")
   
   # 指定要转换的列表字段
   flatten_dict_list_to_rows(json_data, "output.xlsx", list_fields=["列表字段1", "列表字段2"])
   ```

4. **嵌套JSON转多Sheet**：将嵌套JSON转换为多Sheet的Excel文件，每个顶级键作为一个Sheet。
   ```python
   from core.common.json_to_excel import nested_json_to_excel
   
   nested_json_to_excel(json_data, "output.xlsx")
   ```

### 示例

查看 `examples/json_to_excel_example.py` 获取完整示例。
