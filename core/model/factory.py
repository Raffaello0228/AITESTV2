import os
import json
from pathlib import Path
from typing import Dict, Type, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel as PydanticModel, create_model

from core.utils.logger import logger


class ModelFactory:
    """模型工厂类,用于管理所有JSON模板"""

    _instance = None
    _models: Dict[str, Type] = {}
    _templates: Dict[str, dict] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelFactory, cls).__new__(cls)
            cls._instance._load_templates()
        return cls._instance

    def _load_templates(self):
        """加载所有JSON模板文件"""
        template_dir = Path(__file__).parent.parent / "template" / "model"
        if not template_dir.exists():
            logger.warning(f"模板目录不存在: {template_dir}")
            return

        for file_path in template_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    template = json.load(f)
                template_name = file_path.stem
                self._templates[template_name] = template
                logger.debug(f"已加载模板: {template_name}")
            except Exception as e:
                logger.error(f"加载模板失败 {file_path}: {str(e)}")

    @classmethod
    def register(cls, model_name: str = None):
        """注册Model类的装饰器"""

        def decorator(model_class: Type):
            name = model_name or model_class.__name__.lower()
            template = cls._instance._templates.get(name.lower(), {})

            # 先创建一个自定义基类，包含所需配置
            class CustomBaseModel(PydanticModel):
                class Config:
                    validate_assignment = False
                    extra = "allow"  # 允许额外字段
                    arbitrary_types_allowed = True  # 允许任意类型

            # 创建Pydantic模型，使用自定义基类
            fields = {
                key: (Optional[type(value)], None) for key, value in template.items()
            }
            pydantic_model = create_model(
                name,
                **fields,
                __base__=CustomBaseModel,
            )

            cls._models[name] = pydantic_model
            return pydantic_model

        return decorator

    def create_model(self, name: str, **kwargs) -> Optional[object]:
        """创建指定名称的模型实例"""
        model_class = self._models.get(name.lower())
        if model_class is None:
            logger.warning(f"模型类不存在: {name}")
            return None

        try:
            # 处理数据类型转换
            template = self._templates.get(name.lower(), {})
            processed_kwargs = {}

            for key, value in kwargs.items():
                if key in template:
                    template_value = template[key]
                    if isinstance(template_value, (dict, list)):
                        if isinstance(value, str):
                            try:
                                processed_kwargs[key] = json.loads(value)
                            except:
                                processed_kwargs[key] = value
                        else:
                            processed_kwargs[key] = value
                    else:
                        processed_kwargs[key] = value
                else:
                    # 保留不在模板中的字段
                    processed_kwargs[key] = value

            # 使用construct方法创建模型实例，跳过验证
            return model_class.construct(**processed_kwargs)
        except Exception as e:
            logger.error(f"创建模型实例失败 {name}: {str(e)}")
            return None


factory = ModelFactory()
