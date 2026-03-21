"""
农业知识库工具
Agricultural Knowledge Base Tools for LLM Agent
"""

import json
from typing import Optional

# ---------------------------------------------------------------------------
# 静态知识库数据（Phase 1 ~ Phase 2 使用）
# 格式：作物名称 -> {基本参数, 生长周期, 适宜条件, 常见问题}
# Phase 3 替换为 RAG 向量检索
# ---------------------------------------------------------------------------

CROP_KNOWLEDGE = {
    "番茄": {
        "varieties": ["大番茄", "樱桃番茄", "迷你番茄"],
        "growth_cycle_days": {"发芽": 7, "幼苗": 30, "开花": 60, "结果": 90, "成熟": 120},
        "optimal_conditions": {
            "temperature": {"min": 18, "max": 30, "optimal": 25},
            "humidity": {"min": 60, "max": 80, "optimal": 70},
            "light": {"min": 30000, "max": 70000, "optimal": 50000},  # lux
            "co2": {"min": 350, "max": 1000, "optimal": 600},  # ppm
        },
        "soil": {
            "temperature": {"min": 15, "max": 28, "optimal": 22},
            "humidity": {"min": 65, "max": 85, "optimal": 75},
            "ec": {"min": 1.5, "max": 3.5, "optimal": 2.5},
        },
        "common_issues": [
            "灰霉病：高湿度易发，需控制通风",
            "白粉虱：悬挂黄板诱杀，保持温室清洁",
            "裂果：水分供应不均导致，均匀灌溉可预防",
            "畸形果：花期温度异常导致，注意保温",
        ],
        "harvest_notes": "果实转色后即可采收，成熟后及时采摘促进继续结果",
    },
    "黄瓜": {
        "varieties": ["刺黄瓜", "水果黄瓜", "荷兰黄瓜"],
        "growth_cycle_days": {"发芽": 5, "幼苗": 25, "开花": 40, "结果": 55, "成熟": 70},
        "optimal_conditions": {
            "temperature": {"min": 18, "max": 32, "optimal": 28},
            "humidity": {"min": 75, "max": 90, "optimal": 85},
            "light": {"min": 20000, "max": 60000, "optimal": 40000},
            "co2": {"min": 350, "max": 800, "optimal": 500},
        },
        "soil": {
            "temperature": {"min": 18, "max": 30, "optimal": 25},
            "humidity": {"min": 70, "max": 90, "optimal": 80},
            "ec": {"min": 1.8, "max": 3.0, "optimal": 2.3},
        },
        "common_issues": [
            "霜霉病：高湿低温易发，注意通风降湿",
            "白粉病：干燥高温易发，及时摘除病叶",
            "瓜绢螟：生物农药防治，及时清理老叶",
            "弯瓜：营养不良或水分不足导致",
        ],
        "harvest_notes": "达到商品规格及时采收，早期采收有利于后续产量",
    },
    "辣椒": {
        "varieties": ["青椒", "尖椒", "彩椒"],
        "growth_cycle_days": {"发芽": 10, "幼苗": 35, "开花": 70, "结果": 100, "成熟": 130},
        "optimal_conditions": {
            "temperature": {"min": 20, "max": 35, "optimal": 28},
            "humidity": {"min": 60, "max": 80, "optimal": 70},
            "light": {"min": 30000, "max": 80000, "optimal": 50000},
            "co2": {"min": 350, "max": 1000, "optimal": 600},
        },
        "soil": {
            "temperature": {"min": 17, "max": 30, "optimal": 24},
            "humidity": {"min": 60, "max": 80, "optimal": 70},
            "ec": {"min": 1.5, "max": 2.5, "optimal": 2.0},
        },
        "common_issues": [
            "疫病：高温高湿易发，控湿通风是关键",
            "病毒病：蚜虫传播，及时防虫",
            "日灼病：强光直射导致，适当遮阳",
            "落花落果：温度不适或营养不足",
        ],
        "harvest_notes": "青椒达到商品大小即可采收，彩椒需完全转色后采收",
    },
    "草莓": {
        "varieties": ["红颜", "章姬", "法兰地", "白色草莓"],
        "growth_cycle_days": {"发芽": 15, "幼苗": 30, "开花": 60, "结果": 90, "成熟": 120},
        "optimal_conditions": {
            "temperature": {"min": 15, "max": 28, "optimal": 22},
            "humidity": {"min": 60, "max": 80, "optimal": 70},
            "light": {"min": 20000, "max": 50000, "optimal": 35000},
            "co2": {"min": 350, "max": 800, "optimal": 500},
        },
        "soil": {
            "temperature": {"min": 12, "max": 25, "optimal": 18},
            "humidity": {"min": 65, "max": 85, "optimal": 75},
            "ec": {"min": 0.8, "max": 1.5, "optimal": 1.2},
        },
        "common_issues": [
            "灰霉病：高湿易发，及时摘除病果病叶",
            "白粉病：干燥易发，保持适度湿度",
            "红蜘蛛：干燥环境下易发，增加湿度",
            "畸形果：花期授粉不良，注意辅助授粉",
        ],
        "harvest_notes": "果实全面转色后采收，采收时轻拿轻放",
    },
    "生菜": {
        "varieties": ["结球生菜", "散叶生菜", "罗马生菜"],
        "growth_cycle_days": {"发芽": 5, "幼苗": 20, "莲座": 35, "结球": 55, "成熟": 70},
        "optimal_conditions": {
            "temperature": {"min": 10, "max": 25, "optimal": 18},
            "humidity": {"min": 65, "max": 85, "optimal": 75},
            "light": {"min": 15000, "max": 40000, "optimal": 25000},
            "co2": {"min": 350, "max": 800, "optimal": 500},
        },
        "soil": {
            "temperature": {"min": 8, "max": 25, "optimal": 15},
            "humidity": {"min": 65, "max": 85, "optimal": 75},
            "ec": {"min": 0.8, "max": 1.5, "optimal": 1.2},
        },
        "common_issues": [
            "软腐病：高温高湿易发，控湿通风",
            "霜霉病：湿润冷凉环境易发，注意通风",
            "蚜虫：及时发现，生物防治",
            "烧心：钙吸收不良导致，均匀施肥",
        ],
        "harvest_notes": "结球紧实后及时采收，过熟易开裂",
    },
}

# 通用农业知识
GENERAL_KNOWLEDGE = {
    "灌溉原则": "少量多次，保持土壤湿润但不积水。早晨灌溉优于傍晚，减少病害发生。",
    "施肥原则": "基肥为主，追肥为辅。NPK配合使用，中后期增施钾肥促进果实发育。",
    "通风管理": "温室温度超过作物适宜范围上限时，应及时通风降温。通风应循序渐进，避免温度骤变。",
    "光照管理": "光照过强时使用遮阳网，光照不足时使用补光灯。冬季光照不足是主要限制因素。",
    "CO2施肥": "设施内CO2浓度低于350ppm时应补充，适宜浓度600-1000ppm，可显著提高产量。",
}


def query_crop_knowledge(crop_name: str) -> dict:
    """
    查询作物知识库
    """
    crop = CROP_KNOWLEDGE.get(crop_name)
    if not crop:
        available = list(CROP_KNOWLEDGE.keys())
        return {
            "error": f"Knowledge for crop '{crop_name}' not found",
            "available_crops": available,
        }

    return {
        "crop": crop_name,
        "varieties": crop["varieties"],
        "growth_cycle": crop["growth_cycle_days"],
        "optimal_conditions": crop["optimal_conditions"],
        "soil_requirements": crop["soil"],
        "common_issues": crop["common_issues"],
        "harvest_notes": crop["harvest_notes"],
    }


def query_general_agriculture(topic: str) -> dict:
    """
    查询通用农业知识
    """
    result = GENERAL_KNOWLEDGE.get(topic)
    if not result:
        return {
            "error": f"Topic '{topic}' not found",
            "available_topics": list(GENERAL_KNOWLEDGE.keys()),
        }
    return {"topic": topic, "advice": result}


def get_knowledge_tools() -> list[dict]:
    """返回知识库相关的 Tool 定义"""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_crop_knowledge",
                "description": "查询作物的种植知识，包括品种、生长周期、适宜条件、常见问题",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "crop_name": {
                            "type": "string",
                            "description": "作物名称，如：番茄、黄瓜、辣椒、草莓、生菜",
                        },
                    },
                    "required": ["crop_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_agriculture_advice",
                "description": "查询通用农业知识（灌溉、施肥、通风、光照、CO2管理等）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "知识主题",
                            "enum": list(GENERAL_KNOWLEDGE.keys()),
                        },
                    },
                    "required": ["topic"],
                },
            },
        },
    ]
