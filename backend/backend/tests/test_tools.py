"""
工具系统单元测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.tools.sensor_tools import (
    query_latest_sensor_data,
    query_sensor_history,
    get_sensor_tools,
)
from app.tools.device_tools import (
    list_devices,
    get_device_status,
    send_device_command,
    get_device_tools,
)
from app.tools.knowledge_tools import (
    query_crop_knowledge,
    query_general_agriculture,
    get_knowledge_tools,
    CROP_KNOWLEDGE,
)


class TestSensorTools:
    """传感器工具测试"""

    def test_get_sensor_tools_returns_list(self):
        """测试 get_sensor_tools 返回正确结构"""
        tools = get_sensor_tools()
        assert isinstance(tools, list)
        assert len(tools) == 2
        assert tools[0]["function"]["name"] == "get_latest_sensor_data"
        assert tools[1]["function"]["name"] == "get_sensor_history"

    def test_get_sensor_tools_structure(self):
        """测试工具定义结构"""
        tools = get_sensor_tools()
        for tool in tools:
            assert tool["type"] == "function"
            assert "function" in tool
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]


class TestKnowledgeTools:
    """知识库工具测试"""

    def test_get_crop_knowledge_tomato(self):
        """测试番茄知识查询"""
        result = query_crop_knowledge("番茄")
        assert "crop" in result
        assert result["crop"] == "番茄"
        assert "optimal_conditions" in result
        assert "growth_cycle" in result
        assert "common_issues" in result
        assert result["optimal_conditions"]["temperature"]["optimal"] == 25

    def test_get_crop_knowledge_not_found(self):
        """测试未知作物"""
        result = query_crop_knowledge("不存在的作物")
        assert "error" in result
        assert "available_crops" in result
        assert "番茄" in result["available_crops"]

    def test_get_knowledge_tools(self):
        """测试知识库工具定义"""
        tools = get_knowledge_tools()
        assert len(tools) == 2
        tool_names = [t["function"]["name"] for t in tools]
        assert "get_crop_knowledge" in tool_names
        assert "get_agriculture_advice" in tool_names

    def test_all_crops_have_required_fields(self):
        """验证所有作物知识库完整性"""
        required_fields = [
            "varieties",
            "growth_cycle_days",
            "optimal_conditions",
            "soil",
            "common_issues",
            "harvest_notes",
        ]
        for crop_name, crop_data in CROP_KNOWLEDGE.items():
            for field in required_fields:
                assert field in crop_data, f"Crop {crop_name} missing {field}"

    def test_general_agriculture_advice(self):
        """测试通用农业知识查询"""
        result = query_general_agriculture("灌溉原则")
        assert "advice" in result
        assert "灌溉" in result["advice"]

    def test_general_agriculture_not_found(self):
        """测试未知主题"""
        result = query_general_agriculture("不存在的主题")
        assert "error" in result
        assert "available_topics" in result


class TestDeviceTools:
    """设备工具测试"""

    def test_get_device_tools_structure(self):
        """测试设备工具定义"""
        tools = get_device_tools()
        assert len(tools) == 3
        tool_names = [t["function"]["name"] for t in tools]
        assert "list_greenhouse_devices" in tool_names
        assert "get_device_info" in tool_names
        assert "control_device" in tool_names

    def test_control_device_params(self):
        """测试设备控制工具参数"""
        tools = get_device_tools()
        control_tool = next(t for t in tools if t["function"]["name"] == "control_device")
        params = control_tool["function"]["parameters"]
        assert "command" in params["properties"]
        assert params["properties"]["command"]["enum"] == [
            "turn_on",
            "turn_off",
            "set_mode",
            "set_value",
            "reset",
        ]
