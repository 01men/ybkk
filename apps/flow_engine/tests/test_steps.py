"""aios_flow.tests.test_steps —— step 执行器单测。"""
from __future__ import annotations

import asyncio

import pytest

from aios_flow.activities.steps import StepInput, execute_step


def _si(standard_key: str, **kw) -> StepInput:
    return StepInput(
        flow_id="flow-test",
        step_id="s1",
        standard_key=standard_key,
        standard_overrides=kw.get("standard_overrides", {}),
        datasource_bindings=kw.get("datasource_bindings", {}),
        prev_results=[],
        actor="tester",
    )


@pytest.mark.asyncio
async def test_inventory_low_stock_triggers_when_below():
    si = _si("inventory_low_stock", datasource_bindings={"current_stock": 5},
             standard_overrides={"value": 10})
    r = await execute_step(si)
    assert r["matched"] is True
    assert r["output"]["triggered"] is True


@pytest.mark.asyncio
async def test_inventory_low_stock_no_trigger_when_above():
    si = _si("inventory_low_stock", datasource_bindings={"current_stock": 50})
    r = await execute_step(si)
    assert r["matched"] is False


@pytest.mark.asyncio
async def test_notify_purchase_always_matches():
    si = _si("notify_purchase")
    r = await execute_step(si)
    assert r["matched"] is True
    assert r["output"]["notified"] == "purchase-team"


@pytest.mark.asyncio
async def test_create_replenish_ticket_returns_id():
    si = _si("create_replenish_ticket")
    r = await execute_step(si)
    assert r["matched"] is True
    assert r["output"]["ticket_id"].startswith("T-")


@pytest.mark.asyncio
async def test_unknown_standard_returns_error():
    si = _si("nonexistent_standard")
    r = await execute_step(si)
    assert r["matched"] is False
    assert "unknown" in r["error"]


@pytest.mark.asyncio
async def test_equipment_maintenance_due():
    si = _si("equipment_maintenance_due",
             datasource_bindings={"last_maintenance_at": "2026-01-01"})
    r = await execute_step(si)
    assert r["matched"] is True
    assert r["output"]["last_maintenance_at"] == "2026-01-01"


@pytest.mark.asyncio
async def test_inbound_qty_anomaly():
    si = _si("inbound_qty_anomaly",
             datasource_bindings={"received_qty": 80, "ordered_qty": 100})
    r = await execute_step(si)
    assert r["matched"] is True
    assert r["output"]["anomaly"] is True


@pytest.mark.asyncio
async def test_create_8d_report():
    si = _si("create_8d_report")
    r = await execute_step(si)
    assert r["matched"] is True
    assert r["output"]["report_id"].startswith("8D-")


@pytest.mark.asyncio
async def test_all_17_standards_registered():
    """保证 5 场景共 17 个标准全在 STEP_HANDLERS。"""
    from aios_flow.activities.steps import STEP_HANDLERS

    expected = {
        "inventory_low_stock", "notify_purchase", "create_replenish_ticket",
        "equipment_maintenance_due", "create_maintenance_ticket", "notify_maintenance",
        "quality_inspection_sample", "quality_judge_pass", "tag_quality_result",
        "production_collect_constraints", "production_schedule_optimize", "notify_schedule",
        "inbound_qty_anomaly", "inbound_quality_anomaly", "create_8d_report", "notify_supplier",
    }
    assert expected.issubset(STEP_HANDLERS.keys())
    assert len(STEP_HANDLERS) >= 16
