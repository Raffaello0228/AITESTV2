import json
import os
from pathlib import Path

import pandas as pd


class RAGModel:
    def __init__(self, question=None, answer=None, contexts=None, ground_truths=None):
        self.question = question
        self.answer = answer
        self.contexts = contexts
        self.ground_truths = ground_truths
        # 获取API定义文件路径
