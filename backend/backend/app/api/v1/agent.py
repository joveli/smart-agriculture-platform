"""
LLM Agent API - 智能体对话接口
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.agents.greenhouse_agent import GreenhouseAgent


router = APIRouter()


class AgentChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    greenhouse_id: Optional[str] = Field(None, description="当前温室ID（可选）")
    conversation_history: Optional[list[dict]] = Field(default=[], description="历史对话")


class AgentChatResponse(BaseModel):
    reply: str
    tool_calls: list[str]
    turns: int


# 全局 Agent 实例
_agent_instance: Optional[GreenhouseAgent] = None


def get_agent() -> GreenhouseAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = GreenhouseAgent()
    return _agent_instance


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    request: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agent: GreenhouseAgent = Depends(get_agent),
):
    """
    温室智能体对话接口

    支持自然语言查询温室数据、设备控制、告警管理和作物种植知识。
    自动进行 Tool Calling，无需用户指定工具。
    """
    greenhouse_uuid: Optional[UUID] = None
    if request.greenhouse_id:
        try:
            greenhouse_uuid = UUID(request.greenhouse_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid greenhouse_id format")

    result = await agent.chat(
        user_message=request.message,
        db=db,
        tenant_id=current_user.tenant_id,
        greenhouse_id=greenhouse_uuid,
        conversation_history=request.conversation_history or [],
    )

    return AgentChatResponse(
        reply=result["reply"],
        tool_calls=result["tool_calls"],
        turns=result["turns"],
    )


@router.get("/health")
async def agent_health():
    """Agent 服务健康检查"""
    return {"status": "healthy", "model": "MiniMax-2.5"}
