"""
规则引擎单元测试
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.rule_engine import RuleEngine, OPERATORS


class TestRuleEngineOperators:
    """操作符测试"""

    def test_operators(self):
        """测试比较操作符"""
        assert OPERATORS["gt"](5, 3) is True
        assert OPERATORS["gt"](3, 5) is False
        assert OPERATORS["lt"](3, 5) is True
        assert OPERATORS["gte"](5, 5) is True
        assert OPERATORS["lte"](5, 5) is True
        assert OPERATORS["eq"](5, 5) is True
        assert OPERATORS["eq"](5, 6) is False


class TestRuleEngine:
    """RuleEngine 测试"""

    @pytest.fixture
    def engine(self):
        return RuleEngine()

    @pytest.fixture
    def mock_reading(self):
        """创建模拟传感器读数"""
        reading = MagicMock()
        reading.greenhouse_id = uuid4()
        reading.device_id = uuid4()
        reading.tenant_id = uuid4()
        reading.time = datetime.utcnow()
        reading.temperature = 38.5
        reading.humidity = 90.0
        reading.light = 60000
        reading.co2 = 800
        reading.soil_temperature = 30.0
        reading.soil_humidity = 85.0
        reading.soil_ec = 3.0
        return reading

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return AsyncMock()

    def test_build_alert_message_gt(self, engine):
        """测试告警消息构建 - gt"""
        rule = MagicMock()
        rule.metric = "temperature"
        rule.operator = "gt"
        rule.threshold = "35"
        rule.level = "critical"

        message = engine._build_alert_message(rule, 38.5)
        assert "温度" in message
        assert "高于" in message
        assert "35" in message
        assert "38.5" in message

    def test_build_alert_message_lt(self, engine):
        """测试告警消息构建 - lt"""
        rule = MagicMock()
        rule.metric = "humidity"
        rule.operator = "lt"
        rule.threshold = "30"
        rule.level = "warning"

        message = engine._build_alert_message(rule, 25.0)
        assert "湿度" in message
        assert "低于" in message
        assert "30" in message

    def test_build_alert_message_all_levels(self, engine):
        """测试所有告警级别"""
        for level in ["critical", "warning", "info"]:
            rule = MagicMock()
            rule.metric = "temperature"
            rule.operator = "gt"
            rule.threshold = "35"
            rule.level = level
            message = engine._build_alert_message(rule, 38.5)
            assert len(message) > 0


class TestAlertRuleEvaluation:
    """告警规则评估集成测试"""

    @pytest.fixture
    def engine(self):
        return RuleEngine()

    @pytest.mark.asyncio
    async def test_evaluate_no_matching_rules(self, engine):
        """测试无匹配规则时不创建告警"""
        from app.models.alert import AlertRule

        # 模拟传感器读数
        reading = MagicMock()
        reading.greenhouse_id = uuid4()
        reading.device_id = uuid4()
        reading.tenant_id = uuid4()
        reading.temperature = 25.0  # 正常值
        reading.humidity = 70.0

        # 模拟规则（阈值为 35）
        rule = MagicMock(spec=AlertRule)
        rule.metric = "temperature"
        rule.operator = "gt"
        rule.threshold = "35"
        rule.level = "critical"
        rule.greenhouse_id = None
        rule.enabled = True
        rule.cooldown_minutes = 5

        # 模拟数据库
        db = AsyncMock()
        db.execute.return_value.scalar_one_or_none.return_value = [rule]
        db.execute.return_value.scalars.return_value.all.return_value = [rule]
        db.execute.return_value.scalars.return_value.first.return_value = None  # 无最近告警

        result = await engine.evaluate_sensor_reading(db, reading, reading.tenant_id)
        assert len(result) == 0  # 不应触发告警

    @pytest.mark.asyncio
    async def test_should_fire_alert_cooldown(self, engine):
        """测试告警收敛"""
        from app.models.alert import AlertRule

        rule = MagicMock(spec=AlertRule)
        rule.id = uuid4()
        rule.greenhouse_id = uuid4()
        rule.cooldown_minutes = 5

        db = AsyncMock()
        # 模拟最近有告警
        db.execute.return_value.scalars.return_value.first.return_value = MagicMock()

        should_fire = await engine._should_fire_alert(db, rule, rule.greenhouse_id)
        assert should_fire is False  # cooldown 中，不应触发

    @pytest.mark.asyncio
    async def test_should_fire_alert_no_recent(self, engine):
        """测试无最近告警时可触发"""
        from app.models.alert import AlertRule

        rule = MagicMock(spec=AlertRule)
        rule.id = uuid4()
        rule.greenhouse_id = uuid4()
        rule.cooldown_minutes = 5

        db = AsyncMock()
        db.execute.return_value.scalars.return_value.first.return_value = None  # 无最近告警

        should_fire = await engine._should_fire_alert(db, rule, rule.greenhouse_id)
        assert should_fire is True  # 无 cooldown，可触发
