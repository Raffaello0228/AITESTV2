import json
import os
from pathlib import Path

import pandas as pd


class BaseModel:
    def __init__(self, **kwargs):
        # 获取API定义文件路径
        class_name = self.__class__.__name__.lower()
        api_def_path = Path(__file__).parent.parent.parent.parent / 'tests' / 'api_definitions' / f'{class_name}.json'
        
        # 读取API定义文件
        if not api_def_path.exists():
            raise FileNotFoundError(f"API definition file not found: {api_def_path}")
            
        with open(api_def_path, 'r', encoding='utf-8') as f:
            example = json.load(f)
            
        # 设置属性
        for key, value in example.items():
            if key in kwargs:
                v = kwargs.get(key, None)
                if isinstance(value, dict) or isinstance(value, list):
                    if isinstance(v, dict) or isinstance(v, list):
                        setattr(self, key, v)
                    else:
                        setattr(self, key, json.loads(v))
                else:
                    setattr(self, key, kwargs.get(key))
            else:
                setattr(self, key, None)

    @property
    def request(self):
        data = {}
        for k, v in self.__dict__.items():
            if isinstance(v, dict) or isinstance(v, list):
                data.update({k: v})
            elif v and pd.notna(v):
                data.update({k: v})
        return data
