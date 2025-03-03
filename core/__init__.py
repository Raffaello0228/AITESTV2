import os
import sys

# 获取项目根目录
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 将项目根目录添加到Python路径
if root_dir not in sys.path:
    sys.path.append(root_dir)
