"""
Pytest 配置和共享 fixtures
"""

import pytest
import sys
import os

# 确保 app 模块在路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
