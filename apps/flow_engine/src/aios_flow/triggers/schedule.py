"""aios_flow.triggers —— 触发器实现。

- manual: 接收 API 调用 → 启动 workflow（API 端调）
- schedule: APScheduler 每分钟扫 cron 匹配 → 启动 workflow
- ontology_event: V2 占位
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("aios_flow.triggers")


async def start_workflow(
    client,  # temporalio Client
    task_queue: str,
    flow_id: str,
    scenario_id: str,
    flow_template: list[dict],
    standard_overrides: dict,
    datasource_bindings: dict,
    actor: str,
) -> str:
    """启动一个 GenericScenarioWorkflow；返回 workflow_id。"""
    from .workflows.generic import GenericScenarioWorkflow, ScenarioInput

    workflow_id = f"{flow_id}-{int(datetime.now(timezone.utc).timestamp())}"
    await client.start_workflow(
        GenericScenarioWorkflow.run,
        ScenarioInput(
            flow_id=flow_id,
            scenario_id=scenario_id,
            flow_template=flow_template,
            standard_overrides=standard_overrides,
            datasource_bindings=datasource_bindings,
            actor=actor,
        ),
        id=workflow_id,
        task_queue=task_queue,
    )
    return workflow_id


class ScheduleTrigger:
    """APScheduler 包装：每分钟扫一次，匹配 cron 触发。"""

    def __init__(self, get_temporal_client, get_flows, task_queue: str) -> None:
        self._get_temporal_client = get_temporal_client
        self._get_flows = get_flows  # async () -> list[dict]
        self._task_queue = task_queue
        self._scheduler: AsyncIOScheduler | None = None
        self._last_fired: dict[str, str] = {}  # flow_id -> "YYYY-MM-DDTHH:MM"

    async def start(self) -> None:
        self._scheduler = AsyncIOScheduler()
        self._scheduler.add_job(
            self._tick,
            "interval",
            seconds=60,
            id="aios-schedule-trigger",
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info("ScheduleTrigger started (interval=60s)")

    async def stop(self) -> None:
        if self._scheduler:
            self._scheduler.shutdown(wait=False)

    async def _tick(self) -> None:
        try:
            flows = await self._get_flows()
        except Exception as e:  # noqa: BLE001
            logger.warning("get_flows failed: %s", e)
            return
        now = datetime.now()
        for flow in flows:
            if flow.get("trigger_type") != "schedule":
                continue
            cron = (flow.get("trigger_config") or {}).get("cron")
            if not cron:
                continue
            try:
                trigger = CronTrigger.from_crontab(cron)
            except Exception:  # noqa: BLE001
                continue
            # 简单实现：用上次触发的分钟 vs 当前分钟判断
            minute_key = now.strftime("%Y-%m-%dT%H:%M")
            if self._last_fired.get(flow["id"]) == minute_key:
                continue
            if trigger.get_next_fire_time(None, now) and \
               trigger.get_next_fire_time(None, now).replace(second=0, microsecond=0) == now.replace(second=0, microsecond=0):
                self._last_fired[flow["id"]] = minute_key
                try:
                    client = await self._get_temporal_client()
                    await start_workflow(
                        client,
                        self._task_queue,
                        flow["id"],
                        flow["scenario_id"],
                        flow.get("flow_template", []),
                        flow.get("standard_overrides", {}),
                        flow.get("datasource_bindings", {}),
                        actor="schedule",
                    )
                    logger.info("schedule trigger fired: flow=%s", flow["id"])
                except Exception as e:  # noqa: BLE001
                    logger.warning("schedule trigger failed: %s", e)
