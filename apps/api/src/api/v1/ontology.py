"""aios_api.api.v1.ontology —— 本体查询 API（V2）。"""
from __future__ import annotations

import os
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...middleware.auth import CurrentUser

router = APIRouter(prefix="/ontology", tags=["ontology"])


class NodeResponse(BaseModel):
    external_id: str
    kind: str
    props: dict[str, Any]


@router.get("/nodes", response_model=list[NodeResponse], summary="列出本体节点")
async def list_nodes(
    _user: CurrentUser,
    kind: Annotated[str | None, Query()] = None,
    limit: int = Query(100, ge=1, le=500),
) -> list[NodeResponse]:
    ont_url = os.getenv("AIOS_ONTOLOGY_URL", "http://ontology:8083")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{ont_url}/nodes", params={"kind": kind, "limit": limit})
            r.raise_for_status()
            return [NodeResponse(**n) for n in r.json()]
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"ontology service error: {e}") from e


@router.get("/nodes/{external_id}", response_model=NodeResponse, summary="节点详情")
async def get_node(external_id: str, _user: CurrentUser) -> NodeResponse:
    ont_url = os.getenv("AIOS_ONTOLOGY_URL", "http://ontology:8083")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{ont_url}/nodes/{external_id}")
            r.raise_for_status()
            return NodeResponse(**r.json())
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"ontology service error: {e}") from e


@router.get("/nodes/{external_id}/neighbors", summary="邻居节点")
async def get_neighbors(external_id: str, _user: CurrentUser, depth: int = 1) -> dict:
    ont_url = os.getenv("AIOS_ONTOLOGY_URL", "http://ontology:8083")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{ont_url}/nodes/{external_id}/neighbors", params={"depth": depth})
            r.raise_for_status()
            return r.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"ontology service error: {e}") from e
