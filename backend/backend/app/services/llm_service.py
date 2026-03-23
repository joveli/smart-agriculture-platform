"""
LLM 服务层 - MiniMax 2.5 API 封装
LLM Service Layer - MiniMax 2.5 API Wrapper
"""

import json
import httpx
from typing import Optional, Any
from app.core.config import settings


class LLMService:
    """MiniMax 2.5 LLM 服务封装"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.MINIMAX_API_KEY
        self.base_url = base_url or settings.MINIMAX_BASE_URL
        self.model = model or settings.MINIMAX_MODEL
        self.client = httpx.AsyncClient(timeout=60.0)

    async def close(self):
        await self.client.aclose()

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[str] = None,
    ) -> dict:
        """
        通用对话接口

        Args:
            messages: [{"role": "system|user|assistant", "content": "..."}]
            temperature: 随机性控制 (0-1)
            max_tokens: 最大生成长度
            tools: Tool definitions for function calling
            tool_choice: "auto" | "none" 强制使用/不使用工具

        Returns:
            {"content": str, "tool_calls": list[dict]} or {"content": str}
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice

        response = await self.client.post(
            f"{self.base_url}/v1/text/chatcompletion_v2",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        result = response.json()

        # 解析响应
        choice = result.get("choices", [{}])[0]
        message = choice.get("message", {})

        return {
            "content": message.get("content", ""),
            "tool_calls": message.get("tool_calls", []),
            "finish_reason": choice.get("finish_reason", ""),
        }

    async def greenhouse_advisory(
        self,
        greenhouse_data: dict,
        user_question: str,
        conversation_history: Optional[list[dict]] = None,
    ) -> str:
        """
        温室种植建议（领域增强对话）

        Args:
            greenhouse_data: 当前温室传感器数据
            user_question: 用户问题
            conversation_history: 历史对话（可选）

        Returns:
            LLM 回复文本
        """
        system_prompt = """你是一个专业的温室农业顾问。你的职责是：
1. 根据温室实时传感器数据（温度、湿度、光照、CO2、土壤湿度等）提供种植建议
2. 分析异常数据并给出改善建议
3. 解答农户关于作物种植、病虫害防治方面的问题
4. 提供灌溉、通风、遮阳等设备调控建议

注意：
- 如果数据超出作物适宜范围，必须给出预警和建议
- 结合当地气候特点给出实用建议
- 回答要简洁、专业、接地气
"""
        context = f"""当前温室数据：
- 温度：{greenhouse_data.get('temperature', 'N/A')}°C
- 湿度：{greenhouse_data.get('humidity', 'N/A')}%
- 光照：{greenhouse_data.get('light', 'N/A')} lux
- CO2：{greenhouse_data.get('co2', 'N/A')} ppm
- 土壤温度：{greenhouse_data.get('soil_temperature', 'N/A')}°C
- 土壤湿度：{greenhouse_data.get('soil_humidity', 'N/A')}%
- 土壤EC：{greenhouse_data.get('soil_ec', 'N/A')} mS/cm

用户问题：{user_question}"""

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": context})

        result = await self.chat(messages, temperature=0.7)
        return result["content"]

    async def generate_control_suggestion(
        self,
        greenhouse_data: dict,
        current_device_state: dict,
    ) -> str:
        """
        生成设备调控建议（无需用户提问）

        Returns:
            建议文本
        """
        system_prompt = """你是一个温室设备控制专家。根据温室环境数据和当前设备状态，
判断是否需要自动调控，并给出具体建议。

输出格式：
1. 首先判断是否需要调控（是/否）
2. 如果需要，说明调控建议和原因
3. 设备调控需谨慎，只在明确需要时建议开启/关闭设备

设备类型：通风机、遮阳帘、灌溉系统、补光灯、CO2发生器、加温设备
"""
        context = f"""温室数据：{json.dumps(greenhouse_data, ensure_ascii=False)}
当前设备状态：{json.dumps(current_device_state, ensure_ascii=False)}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context},
        ]
        result = await self.chat(messages, temperature=0.3)
        return result["content"]


# 全局单例
llm_service = LLMService()
