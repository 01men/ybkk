"""aios_flow.workflows.generic —— 通用场景 workflow（5 场景共用一个）。"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity, workflow

from .activities.steps import StepInput


@dataclass
class ScenarioInput:
    flow_id: str
    scenario_id: str
    flow_template: list[dict]
    standard_overrides: dict
    datasource_bindings: dict
    actor: str


@dataclass
class ScenarioResult:
    run_id: str
    flow_id: str
    status: str  # success / failed
    step_results: list[dict]
    error: str | None = None


@activity.defn(name="execute_step")
async def execute_step_activity(input: StepInput) -> dict:
    """Activity 包装：调 step 执行器。"""
    from .activities.steps import execute_step

    return await execute_step(input)


@activity.defn(name="record_flow_run")
async def record_flow_run_activity(payload: dict) -> None:
    """V1: 调后端 API 落 flow_runs 表。V2 抽成独立 service。"""
    import httpx

    import os

    api_url = os.getenv("AIOS_API_URL", "http://api:8080")
    cookies = {"aios_token": os.getenv("AIOS_INTERNAL_TOKEN", "")}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{api_url}/api/v1/internal/flow-runs/record",
                json=payload,
                cookies=cookies,
            )
    except Exception as e:  # noqa: BLE001
        # 不阻断主流程；V1 容忍后端不可用
        import logging

        logging.getLogger("aios_flow.workflow").warning("record_flow_run failed: %s", e)


@activity.defn(name="llm_judge")
async def llm_judge_activity(payload: dict) -> dict:
    """V2: LLM 判断 activity 包装。

    payload = {
        "template_key": "quality_defect" | "inbound_anomaly" | "equipment_alert",
        "context": {...},
        "expected_schema": [...],   # 可选
        "actor": "...",
        "run_id": "...",
    }
    返回 dict: {decision, confidence, reasoning, raw_response, duration_ms, llm_call_id}
    """
    from .activities.llm_judge import LLMJudgeInput, llm_judge, get_template

    template = get_template(payload.get("template_key", "equipment_alert"))
    inp = LLMJudgeInput(
        prompt=template,
        context=payload.get("context", {}),
        expected_schema=payload.get("expected_schema", []),
        actor=payload.get("actor", "system"),
        run_id=payload.get("run_id", ""),
    )
    result = await llm_judge(inp)
    return {
        "decision": result.decision,
        "confidence": result.confidence,
        "reasoning": result.reasoning,
        "raw_response": result.raw_response,
        "duration_ms": result.duration_ms,
        "llm_call_id": result.llm_call_id,
    }


@workflow.defn(name="GenericScenarioWorkflow")
class GenericScenarioWorkflow:
    """5 场景共用：按 flow_template 顺序执行每个 step。

    V2 扩展：step.type == "llm_judge" 时改走 llm_judge_activity。
    """

    @workflow.run
    async def run(self, input: ScenarioInput) -> ScenarioResult:
        run_id = str(uuid.uuid4())
        step_results: list[dict] = []
        status = "success"
        error: str | None = None

        # 记录开始
        await workflow.execute_activity(
            record_flow_run_activity,
            {
                "run_id": run_id,
                "flow_id": input.flow_id,
                "status": "running",
                "trigger_type": "manual",
                "actor": input.actor,
                "step_results": [],
            },
            start_to_close_timeout=timedelta(seconds=10),
        )

        for step in input.flow_template:
            step_id = step["id"]
            standard_key = step["standard_key"]
            step_type = step.get("type", "standard")

            try:
                if step_type == "llm_judge":
                    # V2: LLM 判断
                    result = await workflow.execute_activity(
                        llm_judge_activity,
                        {
                            "template_key": step.get("llm_template", "equipment_alert"),
                            "context": {
                                "flow_id": input.flow_id,
                                "step_id": step_id,
                                "standard_key": standard_key,
                                "prev_results": step_results,
                                "datasource_bindings": input.datasource_bindings,
                            },
                            "expected_schema": ["decision", "confidence", "reasoning"],
                            "actor": input.actor,
                            "run_id": run_id,
                        },
                        start_to_close_timeout=timedelta(seconds=120),
                    )
                    step_results.append(
                        {
                            "step_id": step_id,
                            "standard_key": standard_key,
                            "matched": result.get("decision", False),
                            "output": result,
                            "error": None,
                        }
                    )
                else:
                    # V1: 标准 step
                    result = await workflow.execute_activity(
                        execute_step_activity,
                        StepInput(
                            flow_id=input.flow_id,
                            step_id=step_id,
                            standard_key=standard_key,
                            standard_overrides=input.standard_overrides.get(standard_key, {}),
                            datasource_bindings=input.datasource_bindings,
                            prev_results=step_results,
                            actor=input.actor,
                        ),
                        start_to_close_timeout=timedelta(seconds=60),
                    )
                    step_results.append(result)
            except Exception as e:  # noqa: BLE001
                status = "failed"
                error = f"{type(e).__name__}: {e}"
                step_results.append(
                    {
                        "step_id": step_id,
                        "standard_key": standard_key,
                        "matched": False,
                        "output": {},
                        "error": error,
                    }
                )
                break

        # 记录结束
        await workflow.execute_activity(
            record_flow_run_activity,
            {
                "run_id": run_id,
                "flow_id": input.flow_id,
                "status": status,
                "trigger_type": "manual",
                "actor": input.actor,
                "step_results": step_results,
            },
            start_to_close_timeout=timedelta(seconds=10),
        )

        return ScenarioResult(
            run_id=run_id,
            flow_id=input.flow_id,
            status=status,
            step_results=step_results,
            error=error,
        )
