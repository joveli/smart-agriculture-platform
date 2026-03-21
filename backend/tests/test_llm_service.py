"""
LLM Service 单元测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.llm_service import LLMService


class TestLLMService:
    """LLMService 测试用例"""

    @pytest.fixture
    def llm_service(self):
        return LLMService(
            api_key="test-key",
            base_url="https://api.minimax.chat",
            model="MiniMax-2.5-test",
        )

    @pytest.mark.asyncio
    async def test_chat_success(self, llm_service):
        """测试正常对话调用"""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "这是一条测试回复",
                        "tool_calls": [],
                    },
                    "finish_reason": "stop",
                }
            ]
        }

        with patch.object(llm_service.client, "post", return_value=mock_response):
            result = await llm_service.chat(
                messages=[{"role": "user", "content": "你好"}]
            )

        assert result["content"] == "这是一条测试回复"
        assert result["tool_calls"] == []
        assert result["finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_chat_with_tools(self, llm_service):
        """测试带工具调用的对话"""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "call_123",
                                "function": {
                                    "name": "get_latest_sensor_data",
                                    "arguments": '{"greenhouse_id": "test-123"}',
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ]
        }

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_latest_sensor_data",
                    "description": "获取传感器数据",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "greenhouse_id": {"type": "string"},
                        },
                        "required": ["greenhouse_id"],
                    },
                },
            }
        ]

        with patch.object(llm_service.client, "post", return_value=mock_response):
            result = await llm_service.chat(
                messages=[{"role": "user", "content": "当前温度是多少？"}],
                tools=tools,
                tool_choice="auto",
            )

        assert result["content"] == ""
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["function"]["name"] == "get_latest_sensor_data"

    @pytest.mark.asyncio
    async def test_greenhouse_advisory(self, llm_service):
        """测试温室种植建议"""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {"content": "温度偏高，建议开启通风。", "tool_calls": []},
                    "finish_reason": "stop",
                }
            ]
        }

        greenhouse_data = {
            "temperature": 35.5,
            "humidity": 85.0,
            "light": 60000,
            "co2": 500,
            "soil_temperature": 28.0,
            "soil_humidity": 80.0,
            "soil_ec": 2.5,
        }

        with patch.object(llm_service.client, "post", return_value=mock_response):
            result = await llm_service.greenhouse_advisory(
                greenhouse_data=greenhouse_data,
                user_question="温度是否正常？",
            )

        assert "通风" in result

    @pytest.mark.asyncio
    async def test_generate_control_suggestion(self, llm_service):
        """测试设备调控建议生成"""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "是，建议开启通风机降温。",
                        "tool_calls": [],
                    },
                    "finish_reason": "stop",
                }
            ]
        }

        with patch.object(llm_service.client, "post", return_value=mock_response):
            result = await llm_service.generate_control_suggestion(
                greenhouse_data={"temperature": 38.0},
                current_device_state={"fan": "off"},
            )

        assert "通风" in result or "是" in result


class TestLLMServiceEdgeCases:
    """LLMService 边界情况测试"""

    @pytest.fixture
    def llm_service(self):
        return LLMService(
            api_key="test-key",
            base_url="https://api.minimax.chat",
            model="MiniMax-2.5-test",
        )

    @pytest.mark.asyncio
    async def test_chat_timeout(self, llm_service):
        """测试请求超时处理"""
        import httpx

        with patch.object(
            llm_service.client, "post", side_effect=httpx.TimeoutException("timeout")
        ):
            with pytest.raises(httpx.TimeoutException):
                await llm_service.chat(messages=[{"role": "user", "content": "test"}])

    @pytest.mark.asyncio
    async def test_chat_api_error(self, llm_service):
        """测试 API 错误处理"""
        import httpx

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(),
            response=MagicMock(status_code=401),
        )

        with patch.object(llm_service.client, "post", return_value=mock_response):
            with pytest.raises(httpx.HTTPStatusError):
                await llm_service.chat(messages=[{"role": "user", "content": "test"}])
