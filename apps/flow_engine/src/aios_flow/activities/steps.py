"""aios_flow.activities.steps —— 5 个内置场景的 step 执行（V1 同步版，不接 LLM）。"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("aios_flow.steps")


@dataclass
class StepInput:
    flow_id: str
    step_id: str
    standard_key: str
    standard_overrides: dict
    datasource_bindings: dict
    prev_results: list[dict]
    actor: str


@dataclass
class StepResult:
    step_id: str
    standard_key: str
    matched: bool
    output: dict
    error: str | None = None


async def execute_step(input: StepInput) -> dict:
    """5 场景共 17 个标准的 step 执行器。"""
    handler = STEP_HANDLERS.get(input.standard_key)
    if handler is None:
        return StepResult(
            step_id=input.step_id,
            standard_key=input.standard_key,
            matched=False,
            output={},
            error=f"unknown standard_key: {input.standard_key}",
        ).__dict__
    try:
        result = await handler(input)
        return result.__dict__
    except Exception as e:
        logger.exception("step failed: %s", input.standard_key)
        return StepResult(
            step_id=input.step_id,
            standard_key=input.standard_key,
            matched=False,
            output={},
            error=f"{type(e).__name__}: {e}",
        ).__dict__


# -----------------------------------------------------------------------------
# 5 场景的标准实现（V1 同步版：查 ontology 字段 / 比阈值 / 占位 notify）
# -----------------------------------------------------------------------------


async def _inventory_low_stock(input: StepInput) -> StepResult:
    """V1 简化：直接读 input.datasource_bindings 里的阈值（演示用）。"""
    threshold = input.standard_overrides.get("value", 10)
    current = input.datasource_bindings.get("current_stock", 0)
    matched = current < threshold
    return StepResult(
        step_id=input.step_id,
        standard_key=input.standard_key,
        matched=matched,
        output={"current_stock": current, "threshold": threshold, "triggered": matched},
    )


async def _notify_purchase(input: StepInput) -> StepResult:
    """V1: console.log 占位。V2 接飞书/钉钉/邮件。"""
    logger.info(
        "[NOTIFY-PURCHASE] actor=%s flow=%s prev=%s",
        input.actor,
        input.flow_id,
        input.prev_results,
    )
    return StepResult(
        step_id=input.step_id,
        standard_key=input.standard_key,
        matched=True,
        output={"notified": "purchase-team", "channel": "console"},
    )


async def _create_replenish_ticket(input: StepInput) -> StepResult:
    """V1: 占位，V2 接工单系统。"""
    ticket_id = f"T-{input.flow_id[:8]}"
    return StepResult(
        step_id=input.step_id,
        standard_key=input.standard_key,
        matched=True,
        output={"ticket_id": ticket_id, "ticket_type": "replenish"},
    )


async def _equipment_maintenance_due(input: StepInput) -> StepResult:
    last = input.datasource_bindings.get("last_maintenance_at")
    return StepResult(
        step_id=input.step_id,
        standard_key=input.standard_key,
        matched=True,
        output={"last_maintenance_at": last, "due": True},
    )


async def _create_maintenance_ticket(input: StepInput) -> StepResult:
    ticket_id = f"M-{input.flow_id[:8]}"
    return StepResult(
        step_id=input.step_id,
        standard_key=input.standard_key,
        matched=True,
        output={"ticket_id": ticket_id, "ticket_type": "maintenance"},
    )


async def _notify_maintenance(input: StepInput) -> StepResult:
    logger.info("[NOTIFY-MAINT] actor=%s flow=%s", input.actor, input.flow_id)
    return StepResult(
        step_id=input.step_id,
        standard_key=input.standard_key,
        matched=True,
        output={"notified": "maintenance-team", "channel": "console"},
    )


async def _quality_inspection_sample(input: StepInput) -> StepResult:
    return StepResult(
        step_id=input.step_id,
        standard_key=input.standard_key,
        matched=True,
        output={"aql": "2.5", "sample_size": 5},
    )


async def _quality_judge_pass(input: StepInput) -> StepResult:
    return StepResult(
        step_id=input.step_id,
        standard_key=input.standard_key,
        matched=True,
        output={"passed": True},
    )


async def _tag_quality_result(input: StepInput) -> StepResult:
    return StepResult(
        step_id=input.step_id,
        standard_key=input.standard_key,
        matched=True,
        output={"tag": "quality:passed"},
    )


async def _production_collect_constraints(input: StepInput) -> StepResult:
    return StepResult(
        step_id=input.step_id,
        standard_key=input.standard_key,
        matched=True,
        output={"orders": 0, "capacity": 0, "materials": 0},
    )


async def _production_schedule_optimize(input: StepInput) -> StepResult:
    return StepResult(
        step_id=input.step_id,
        standard_key=input.standard_key,
        matched=True,
        output={"plan": "linear", "tag": "urgent"},
    )


async def _notify_schedule(input: StepInput) -> StepResult:
    logger.info("[NOTIFY-SCHEDULE] actor=%s flow=%s", input.actor, input.flow_id)
    return StepResult(
        step_id=input.step_id,
        standard_key=input.standard_key,
        matched=True,
        output={"notified": "workshop", "channel": "console"},
    )


async def _inbound_qty_anomaly(input: StepInput) -> StepResult:
    received = input.datasource_bindings.get("received_qty", 0)
    ordered = input.datasource_bindings.get("ordered_qty", 0)
    matched = received < ordered
    return StepResult(
        step_id=input.step_id,
        standard_key=input.standard_key,
        matched=matched,
        output={"received_qty": received, "ordered_qty": ordered, "anomaly": matched},
    )


async def _inbound_quality_anomaly(input: StepInput) -> StepResult:
    return StepResult(
        step_id=input.step_id,
        standard_key=input.standard_key,
        matched=False,
        output={"defect_rate": 0.01},
    )


async def _create_8d_report(input: StepInput) -> StepResult:
    report_id = f"8D-{input.flow_id[:8]}"
    return StepResult(
        step_id=input.step_id,
        standard_key=input.standard_key,
        matched=True,
        output={"report_id": report_id},
    )


async def _notify_supplier(input: StepInput) -> StepResult:
    logger.info("[NOTIFY-SUPPLIER] actor=%s flow=%s", input.actor, input.flow_id)
    return StepResult(
        step_id=input.step_id,
        standard_key=input.standard_key,
        matched=True,
        output={"notified": "supplier", "channel": "console"},
    )


STEP_HANDLERS: dict[str, Any] = {
    "inventory_low_stock": _inventory_low_stock,
    "notify_purchase": _notify_purchase,
    "create_replenish_ticket": _create_replenish_ticket,
    "equipment_maintenance_due": _equipment_maintenance_due,
    "create_maintenance_ticket": _create_maintenance_ticket,
    "notify_maintenance": _notify_maintenance,
    "quality_inspection_sample": _quality_inspection_sample,
    "quality_judge_pass": _quality_judge_pass,
    "tag_quality_result": _tag_quality_result,
    "production_collect_constraints": _production_collect_constraints,
    "production_schedule_optimize": _production_schedule_optimize,
    "notify_schedule": _notify_schedule,
    "inbound_qty_anomaly": _inbound_qty_anomaly,
    "inbound_quality_anomaly": _inbound_quality_anomaly,
    "create_8d_report": _create_8d_report,
    "notify_supplier": _notify_supplier,
}
