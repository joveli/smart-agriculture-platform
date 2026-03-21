"""
温室智能体 - Greenhouse Agent with Function Calling
基于 MiniMax 2.5 的温室农业智能助手
"""

import json
from uuid import UUID
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm_service import LLMService
from app.tools import (
    get_sensor_tools,
    get_device_tools,
    get_alert_tools,
    get_knowledge_tools,
)
from app.tools.sensor_tools import query_latest_sensor_data, query_sensor_history
from app.tools.device_tools import list_devices, get_device_status, send_device_command
from app.tools.alert_tools import list_alerts, create_alert_rule, get_alert_summary
from app.tools.knowledge_tools import query_crop_knowledge, query_general_agriculture


# 合并所有工具定义
ALL_TOOLS = (
    get_sensor_tools()
    + get_device_tools()
    + get_alert_tools()
    + get_knowledge_tools()
)

# Tool name -> async function mapping
TOOL_HANDLERS = {
    "get_latest_sensor_data": query_latest_sensor_data,
    "get_sensor_history": query_sensor_history,
    "list_greenhouse_devices": list_devices,
    "get_device_info": get_device_status,
    "control_device": send_device_command,
    "get_alert_summary": get_alert_summary,
    "list_alerts": list_alerts,
    "create_alert_rule": create_alert_rule,
    "get_crop_knowledge": query_crop_knowledge,
    "get_agriculture_advice": query_general_agriculture,
}


class GreenhouseAgent:
    """
    温室农业智能体

    支持：
    - 自然语言问答（温室数据查询、设备控制、告警管理）
    - Tool Calling（自动调用工具获取实时数据）
    - 作物种植知识查询
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()
        self.tools = ALL_TOOLS

    async def chat(
        self,
        user_message: str,
        db: AsyncSession,
        tenant_id: UUID,
        greenhouse_id: Optional[UUID] = None,
        conversation_history: Optional[list[dict]] = None,
        max_turns: int = 10,
    ) -> dict:
        """
        处理用户消息，执行 Tool Calling 循环

        Args:
            user_message: 用户输入
            db: 数据库会话
            tenant_id: 当前租户 ID
            greenhouse_id: 当前温室 ID（可选）
            conversation_history: 历史对话
            max_turns: 最大 Tool Call 轮次（防止无限循环）

        Returns:
            {"reply": str, "tool_calls": list[str], "turns": int}
        """
        messages = [{"role": "system", "content": self._system_prompt()}]
        if conversation_history:
            messages.extend(conversation_history)

        # 将温室上下文注入到用户消息中
        context_parts = []
        if greenhouse_id:
            context_parts.append(f"当前温室ID: {greenhouse_id}")
        context_parts.append(f"租户ID: {tenant_id}")
        if context_parts:
            user_message = f"[{', '.join(context_parts)}]\n\n{user_message}"

        messages.append({"role": "user", "content": user_message})

        tool_call_list = []
        turns = 0

        while turns < max_turns:
            turns += 1

            # 调用 LLM（带 tools）
            response = await self.llm.chat(
                messages=messages,
                temperature=0.7,
                tools=self.tools,
                tool_choice="auto",
            )

            assistant_message = response["content"]
            tool_calls = response.get("tool_calls", [])

            # 添加 LLM 回复到对话
            messages.append({"role": "assistant", "content": assistant_message})

            if not tool_calls:
                # 没有更多 tool calls，结束
                break

            # 处理每个 tool call
            for call in tool_calls:
                tool_name = call.get("function", {}).get("name", "")
                tool_args = json.loads(call.get("function", {}).get("arguments", "{}"))
                tool_call_list.append(tool_name)

                # 注入 tenant_id 和 db 到参数
                tool_args["tenant_id"] = tenant_id
                if "greenhouse_id" in tool_args and greenhouse_id:
                    # 如果用户没有指定温室，使用当前温室
                    if not tool_args["greenhouse_id"]:
                        tool_args["greenhouse_id"] = greenhouse_id

                # 获取处理器
                handler = TOOL_HANDLERS.get(tool_name)
                if not handler:
                    tool_result = {"error": f"Unknown tool: {tool_name}"}
                else:
                    try:
                        # 调用工具（db 需要特殊处理）
                        if tool_name in ("get_latest_sensor_data", "get_sensor_history",
                                         "list_greenhouse_devices", "get_device_info",
                                         "control_device", "get_alert_summary",
                                         "list_alerts"):
                            tool_result = await handler(db=db, **tool_args)
                        else:
                            # 知识库工具不需要 db
                            tool_result = await handler(**{k: v for k, v in tool_args.items() if k != "db"})
                    except Exception as e:
                        tool_result = {"error": str(e)}

                # 将工具结果添加到对话
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.get("id", ""),
                    "name": tool_name,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                })

        return {
            "reply": assistant_message,
            "tool_calls": tool_call_list,
            "turns": turns,
        }

    def _system_prompt(self) -> str:
        return """你是一个专业的温室农业智能助手。你的能力包括：

1. **传感器数据查询**：可以查询温室的温度、湿度、光照、CO2、土壤温湿度等实时和历史数据
2. **设备管理**：可以查询设备状态、向设备发送控制指令（通风、灌溉、遮阳等）
3. **告警管理**：可以查询告警统计、创建告警规则
4. **种植知识**：掌握番茄、黄瓜、辣椒、草莓、生菜等作物的种植知识

**使用指南**：
- 当用户询问温室当前环境数据时，调用 `get_latest_sensor_data`
- 当用户需要分析历史趋势时，调用 `get_sensor_history`
- 当用户询问作物种植问题时，调用 `get_crop_knowledge`
- 当用户询问通用农业知识（灌溉、施肥等）时，调用 `get_agriculture_advice`
- 当用户需要控制设备时，先查询设备状态再发送指令

**回答原则**：
- 专业、简洁、接地气
- 数据超出适宜范围时必须给出预警和建议
- 不确定时调用工具获取实时数据，不要编造数据
"""
