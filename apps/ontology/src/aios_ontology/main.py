"""aios_ontology.main —— 本体服务 FastAPI。"""
from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Body, FastAPI, HTTPException, Query
from neo4j import GraphDatabase
from pydantic import BaseModel

from .config import get_settings
from .extractor import extract_entities, extract_relations
from .schema import init_schema

logger = logging.getLogger("aios_ontology.api")


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    )
    app.state.settings = settings
    app.state.driver = GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )
    init_schema(app.state.driver)
    logger.info("aios-ontology API 启动")
    yield
    app.state.driver.close()


app = FastAPI(title="aios-ontology", version="0.2.0", lifespan=lifespan)


class NodeResponse(BaseModel):
    external_id: str
    kind: str
    props: dict[str, Any]


class NeighborResponse(BaseModel):
    node: dict[str, Any]
    neighbors: list[dict[str, Any]]


class CypherRequest(BaseModel):
    query: str
    params: dict[str, Any] = {}


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.get("/nodes", response_model=list[NodeResponse])
async def list_nodes(
    kind: Annotated[str | None, Query()] = None,
    limit: int = 100,
) -> list[NodeResponse]:
    cypher = "MATCH (n) WHERE $kind IS NULL OR label(n) = $kind RETURN n LIMIT $limit"
    out: list[NodeResponse] = []
    with app.state.driver.session() as session:
        for record in session.run(cypher, kind=kind, limit=limit):
            n = record["n"]
            labels = list(n.labels) if hasattr(n, "labels") else []
            kind_str = labels[0] if labels else "Unknown"
            out.append(
                NodeResponse(
                    external_id=str(n.get("external_id", "")),
                    kind=kind_str,
                    props={k: str(v) for k, v in dict(n).items()},
                )
            )
    return out


@app.get("/nodes/{external_id}", response_model=NodeResponse)
async def get_node(external_id: str) -> NodeResponse:
    cypher = "MATCH (n {external_id: $eid}) RETURN n"
    with app.state.driver.session() as session:
        record = session.run(cypher, eid=external_id).single()
        if record is None:
            raise HTTPException(status_code=404, detail="node not found")
        n = record["n"]
        labels = list(n.labels) if hasattr(n, "labels") else []
        kind_str = labels[0] if labels else "Unknown"
        return NodeResponse(
            external_id=str(n.get("external_id", "")),
            kind=kind_str,
            props={k: str(v) for k, v in dict(n).items()},
        )


@app.get("/nodes/{external_id}/neighbors", response_model=NeighborResponse)
async def get_neighbors(external_id: str, depth: int = 1) -> NeighborResponse:
    cypher = (
        f"MATCH (n {{external_id: $eid}})-[r*1..{depth}]-(m) "
        "RETURN n, m, type(r) AS rel_type LIMIT 50"
    )
    with app.state.driver.session() as session:
        records = list(session.run(cypher, eid=external_id))
        if not records:
            raise HTTPException(status_code=404, detail="node not found")
        n = records[0]["n"]
        node_dict = dict(n)
        node_dict["_labels"] = list(n.labels)
        neighbors = []
        for r in records:
            m = r["m"]
            md = dict(m)
            md["_labels"] = list(m.labels)
            md["_rel_type"] = r["rel_type"]
            neighbors.append(md)
    return NeighborResponse(node=node_dict, neighbors=neighbors)


@app.post("/query")
async def query_cypher(body: CypherRequest) -> dict:
    """受控 Cypher 查询（V2 限制：仅允许 MATCH / RETURN / WHERE）。"""
    forbidden = ["CREATE", "DELETE", "SET", "REMOVE", "MERGE", "DROP", "CALL", "LOAD"]
    upper = body.query.upper()
    for kw in forbidden:
        if kw in upper:
            raise HTTPException(status_code=403, detail=f"forbidden keyword: {kw}")
    with app.state.driver.session() as session:
        result = session.run(body.query, **body.params)
        return {"rows": [dict(r) for r in result]}


@app.post("/ingest/extract")
async def extract_from_text(payload: dict[str, str]) -> dict:
    """从纯文本抽取实体 + 关系（不写库）。"""
    text = payload.get("text", "")
    entities = extract_entities(text)
    relations = extract_relations(entities)
    return {"entities": entities, "relations": relations}


@app.post("/ingest/upsert")
async def upsert_entities(payload: dict) -> dict:
    """把实体 + 关系写入 Neo4j。"""
    entities = payload.get("entities", [])
    relations = payload.get("relations", [])
    written = 0
    with app.state.driver.session() as session:
        for e in entities:
            kind = e.get("kind", "Unknown")
            external_id = e.get("external_id") or str(uuid.uuid4())
            props = {k: v for k, v in e.items() if k not in ("kind",)}
            props["external_id"] = external_id
            cypher = f"MERGE (n:{kind} {{external_id: $external_id}}) SET n += $props"
            session.run(cypher, external_id=external_id, props=props)
            written += 1
        for r in relations:
            rtype = r.get("type", "RELATED_TO")
            frm = r.get("from")
            to = r.get("to")
            if not frm or not to:
                continue
            cypher = (
                f"MATCH (a {{external_id: $frm}}), (b {{external_id: $to}}) "
                f"MERGE (a)-[r:{rtype}]->(b)"
            )
            session.run(cypher, frm=frm, to=to)
    return {"written_nodes": written, "written_relations": len(relations)}
