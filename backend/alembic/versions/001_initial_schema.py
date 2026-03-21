"""
初始数据库迁移
Initial Database Migration - All tables + TimescaleDB hypertable
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === 租户表 ===
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("contact_email", sa.String(255), nullable=False, unique=True),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        sa.Column("plan_type", sa.String(50), server_default="free"),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("storage_quota_gb", sa.String(20), server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )

    # === 用户表 ===
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("username", sa.String(100), unique=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("role", sa.String(50), nullable=False, server_default="farmer"),
        sa.Column("is_active", sa.Boolean(), server_default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Index("ix_users_tenant_id", "tenant_id"),
    )

    # === 套餐表 ===
    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("price_monthly", sa.Numeric(10, 2), server_default="0"),
        sa.Column("price_yearly", sa.Numeric(10, 2), nullable=True),
        sa.Column("device_limit", sa.Integer(), server_default="5"),
        sa.Column("data_point_limit", sa.Integer(), server_default="100000"),
        sa.Column("api_call_limit", sa.Integer(), server_default="10000"),
        sa.Column("alert_limit", sa.Integer(), server_default="50"),
        sa.Column("storage_gb_limit", sa.Numeric(10, 2), server_default="1"),
        sa.Column("user_limit", sa.Integer(), server_default="3"),
        sa.Column("device_overage", sa.Numeric(10, 2), server_default="20"),
        sa.Column("data_point_overage", sa.Numeric(10, 4), server_default="0.00005"),
        sa.Column("api_call_overage", sa.Numeric(10, 5), server_default="0.0001"),
        sa.Column("alert_overage", sa.Numeric(10, 4), server_default="0.01"),
        sa.Column("storage_overage", sa.Numeric(10, 2), server_default="2"),
        sa.Column("is_active", sa.Boolean(), server_default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # === 租户套餐表 ===
    op.create_table(
        "tenant_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, unique=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("is_trial", sa.Boolean(), server_default=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Index("ix_tenant_plans_tenant_id", "tenant_id"),
    )

    # === 农场表 ===
    op.create_table(
        "farms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("area_mu", sa.Numeric(10, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Index("ix_farms_tenant_id", "tenant_id"),
    )

    # === 作物表 ===
    op.create_table(
        "crops",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("variety", sa.String(255), nullable=True),
        sa.Column("growth_cycle_days", sa.Integer(), nullable=True),
        sa.Column("optimal_temp_min", sa.Numeric(5, 2), nullable=True),
        sa.Column("optimal_temp_max", sa.Numeric(5, 2), nullable=True),
        sa.Column("optimal_humidity_min", sa.Numeric(5, 2), nullable=True),
        sa.Column("optimal_humidity_max", sa.Numeric(5, 2), nullable=True),
        sa.Column("optimal_light_min", sa.Numeric(10, 2), nullable=True),
        sa.Column("optimal_light_max", sa.Numeric(10, 2), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # === 温室表 ===
    op.create_table(
        "greenhouses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("farms.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("crop_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crops.id"), nullable=True),
        sa.Column("area_sqm", sa.Numeric(10, 2), nullable=True),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Index("ix_greenhouses_tenant_id", "tenant_id"),
        sa.Index("ix_greenhouses_farm_id", "farm_id"),
    )

    # === 设备表 ===
    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("greenhouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("greenhouses.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("device_type", sa.String(50), nullable=False, server_default="sensor"),
        sa.Column("model", sa.String(255), nullable=True),
        sa.Column("sn", sa.String(255), unique=True, nullable=True),
        sa.Column("manufacturer", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), server_default="offline"),
        sa.Column("mqtt_topic", sa.String(500), nullable=True),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.Column("calibration_offset", sa.Numeric(10, 4), nullable=True),
        sa.Column("sampling_interval_sec", sa.Integer(), server_default="60"),
        sa.Column("is_active", sa.Boolean(), server_default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Index("ix_devices_tenant_id", "tenant_id"),
        sa.Index("ix_devices_greenhouse_id", "greenhouse_id"),
    )

    # === 传感器时序数据表（普通表，后续转为 hypertable）===
    op.create_table(
        "sensor_readings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("greenhouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("greenhouses.id"), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("time", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("temperature", sa.Numeric(8, 3), nullable=True),
        sa.Column("humidity", sa.Numeric(8, 3), nullable=True),
        sa.Column("light", sa.Numeric(12, 2), nullable=True),
        sa.Column("co2", sa.Numeric(10, 2), nullable=True),
        sa.Column("soil_temperature", sa.Numeric(8, 3), nullable=True),
        sa.Column("soil_humidity", sa.Numeric(8, 3), nullable=True),
        sa.Column("soil_ec", sa.Numeric(10, 4), nullable=True),
        sa.Column("raw_payload", sa.String(1000), nullable=True),
        sa.Index("ix_sensor_readings_tenant_time", "tenant_id", "time"),
        sa.Index("ix_sensor_readings_greenhouse_time", "greenhouse_id", "time"),
    )

    # === 转换为 TimescaleDB 超表 ===
    # 注意：此 SQL 需 TimescaleDB 扩展
    op.execute("""
        SELECT create_hypertable('sensor_readings', 'time',
            chunk_time_interval => INTERVAL '1 month',
            migrate_data => true
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_sensor_readings_tenant_time
            ON sensor_readings (tenant_id, time DESC);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_sensor_readings_greenhouse_time
            ON sensor_readings (greenhouse_id, time DESC);
    """)

    # === 告警规则表 ===
    op.create_table(
        "alert_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("greenhouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("greenhouses.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("operator", sa.String(10), nullable=False),
        sa.Column("threshold", sa.String(50), nullable=False),
        sa.Column("level", sa.String(20), server_default="warning"),
        sa.Column("enabled", sa.Boolean(), server_default=True),
        sa.Column("notification_channels", postgresql.JSONB, nullable=True),
        sa.Column("cooldown_minutes", sa.Integer(), server_default="5"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Index("ix_alert_rules_tenant_id", "tenant_id"),
    )

    # === 告警记录表 ===
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("greenhouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("greenhouses.id"), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id"), nullable=True),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("alert_rules.id"), nullable=True),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metric_value", sa.String(50), nullable=True),
        sa.Column("threshold_value", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("notification_sent", sa.Boolean(), server_default=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Index("ix_alerts_tenant_id", "tenant_id"),
        sa.Index("ix_alerts_created_at", "created_at"),
    )

    # === 资源使用量记录表 ===
    op.create_table(
        "usage_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("period_month", sa.String(7), nullable=False),
        sa.Column("usage_value", sa.Numeric(20, 4), server_default="0"),
        sa.Column("overage_value", sa.Numeric(20, 4), server_default="0"),
        sa.Column("overage_cost", sa.Numeric(10, 2), server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Index("ix_usage_records_tenant_id", "tenant_id"),
        sa.Index("ix_usage_records_period_month", "period_month"),
        sa.UniqueConstraint("tenant_id", "resource_type", "period_month", name="ix_usage_tenant_resource_month"),
    )

    # === 审计日志表 ===
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("request_method", sa.String(10), nullable=True),
        sa.Column("request_path", sa.String(500), nullable=True),
        sa.Column("request_body", postgresql.JSONB, nullable=True),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("client_ip", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Index("ix_audit_logs_tenant_id", "tenant_id"),
        sa.Index("ix_audit_logs_user_id", "user_id"),
        sa.Index("ix_audit_logs_created_at", "created_at"),
    )

    # === 插入默认套餐 ===
    op.execute("""
        INSERT INTO plans (id, name, display_name, price_monthly,
            device_limit, data_point_limit, api_call_limit, alert_limit,
            storage_gb_limit, user_limit)
        VALUES
            (gen_random_uuid(), 'free', '免费版', 0, 5, 100000, 10000, 50, 1, 3),
            (gen_random_uuid(), 'standard', '标准版', 299, 50, 1000000, 200000, 500, 20, 20),
            (gen_random_uuid(), 'premium', '高级版', 999, 200, 5000000, 1000000, 2000, 100, 100),
            (gen_random_uuid(), 'enterprise', '企业版', 0, -1, -1, -1, -1, -1, -1)
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("usage_records")
    op.drop_table("alerts")
    op.drop_table("alert_rules")
    op.drop_table("sensor_readings")
    op.drop_table("devices")
    op.drop_table("greenhouses")
    op.drop_table("crops")
    op.drop_table("farms")
    op.drop_table("tenant_plans")
    op.drop_table("plans")
    op.drop_table("users")
    op.drop_table("tenants")
