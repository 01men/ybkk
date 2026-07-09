"""aios_api.models —— SQLAlchemy ORM 模型（参见 02-design-doc.md §2.3）。"""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


class DatasourceStatus(str, enum.Enum):
    PENDING = "pending"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"
    DISABLED = "disabled"


class FlowStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class FlowRunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Datasource(Base):
    """数据源注册表。

    关键约束：
      - connection_json 加密存储（调用 KMS 解密后才连接）
      - read_only_account_ack 必须为 True 才能连接
      - 不存明文密码
    """

    __tablename__ = "datasources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    connection_json_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DatasourceStatus] = mapped_column(
        Enum(DatasourceStatus, name="datasource_status"),
        nullable=False,
        default=DatasourceStatus.PENDING,
        index=True,
    )
    last_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Datasource {self.id} type={self.type} status={self.status}>"


class DeliveryStandard(Base):
    """交付标准表。

    关键约束：
      - built_in=True 表示平台内置，不可删
      - scope_json 限定适用范围（按角色 / 场景 / 数据源类型）
      - expr_json 是标准表达式（DSL）
    """

    __tablename__ = "delivery_standards"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    expr_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    scope_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    built_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (Index("ix_standards_tenant_key", "tenant_id", "key"),)


class Scenario(Base):
    """场景模板表。"""

    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    industry: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    default_standard_keys: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    flow_template_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    built_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Flow(Base):
    """用户创建的 AI 业务流程。"""

    __tablename__ = "flows"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("scenarios.id"), nullable=False, index=True
    )
    datasource_bindings_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    standard_overrides_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[FlowStatus] = mapped_column(
        Enum(FlowStatus, name="flow_status"),
        nullable=False,
        default=FlowStatus.DRAFT,
        index=True,
    )
    created_by: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    runs: Mapped[list[FlowRun]] = relationship(back_populates="flow", cascade="all, delete-orphan")


class FlowRun(Base):
    """流程执行历史。"""

    __tablename__ = "flow_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    flow_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("flows.id"), nullable=False, index=True
    )
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[FlowRunStatus] = mapped_column(
        Enum(FlowRunStatus, name="flow_run_status"),
        nullable=False,
        default=FlowRunStatus.PENDING,
        index=True,
    )
    output_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    audit_ref: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    flow: Mapped[Flow] = relationship(back_populates="runs")

    __table_args__ = (Index("ix_runs_flow_triggered", "flow_id", "triggered_at"),)


class AuditLog(Base):
    """审计日志（append-only）。

    触发器禁止 UPDATE / DELETE（在 migration 中建）。
    """

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    actor: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    datasource_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    standard_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    flow_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    hash_chain: Mapped[str] = mapped_column(String(128), nullable=False)

    __table_args__ = (Index("ix_audit_ts_desc", "ts"),)