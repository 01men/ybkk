"""aios_flow.worker —— Temporal Worker 入口。"""
from __future__ import annotations

import asyncio
import logging
import signal

from temporalio.client import Client
from temporalio.worker import Worker

from .activities.steps import execute_step_activity, record_flow_run_activity
from .config import get_settings
from .triggers.schedule import ScheduleTrigger
from .workflows.generic import GenericScenarioWorkflow

logger = logging.getLogger("aios_flow.worker")


async def _list_flows_via_api() -> list[dict]:
    """从后端 API 拉所有 trigger_type=schedule 的 flow。"""
    import os

    import httpx

    api_url = os.getenv("AIOS_API_URL", "http://api:8080")
    token = os.getenv("AIOS_INTERNAL_TOKEN", "")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{api_url}/api/v1/internal/flows/schedule-eligible",
                cookies={"aios_token": token},
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:  # noqa: BLE001
        logger.warning("list_flows_via_api failed: %s", e)
        return []


async def main() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    )
    logger.info("aios-flow-engine %s 启动", settings.app_version)

    client = await Client.connect(settings.temporal_host, namespace=settings.temporal_namespace)

    worker = Worker(
        client,
        task_queue=settings.task_queue,
        workflows=[GenericScenarioWorkflow],
        activities=[execute_step_activity, record_flow_run_activity],
    )

    # 启动 schedule 触发器
    if settings.scheduler_enabled:

        async def get_client():
            return client

        trigger = ScheduleTrigger(get_client, _list_flows_via_api, settings.task_queue)
        await trigger.start()

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _on_signal():
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _on_signal)
        except NotImplementedError:
            pass  # Windows

    async def run_worker():
        await worker.run()

    worker_task = asyncio.create_task(run_worker())
    await stop_event.wait()
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    logger.info("aios-flow-engine 关闭")


if __name__ == "__main__":
    asyncio.run(main())
