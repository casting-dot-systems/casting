from __future__ import annotations

from typing import Dict, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from casting.cast.core.models import CastConfig


class AgentRegistration(BaseModel):
    agent_name: str
    cast_config: CastConfig


class AgentRecord(BaseModel):
    agent_id: str
    agent_name: str
    cast_config: CastConfig


app = FastAPI(title="Casting Org Agent Hub", version="0.1.0")

_agents: Dict[str, AgentRecord] = {}


def _seed_agents() -> None:
    seeds: List[AgentRegistration] = [
        AgentRegistration(
            agent_name="sync-watchdog",
            cast_config=CastConfig.model_validate(
                {
                    "id": "a7f0c8e1-0c24-4dc4-8e7f-b3e1f5e76001",
                    "cast-name": "Casting Systems",
                }
            ),
        ),
        AgentRegistration(
            agent_name="daily-digest",
            cast_config=CastConfig.model_validate(
                {
                    "id": "c1e79f13-9bb0-4d9d-b5d2-fbda94e0a4b2",
                    "cast-name": "Casting Systems R&D",
                }
            ),
        ),
    ]
    for seed in seeds:
        agent_id = str(uuid4())
        _agents[agent_id] = AgentRecord(
            agent_id=agent_id,
            agent_name=seed.agent_name,
            cast_config=seed.cast_config,
        )


_seed_agents()


@app.post("/agents", response_model=AgentRecord)
def register_agent(payload: AgentRegistration) -> AgentRecord:
    agent_id = str(uuid4())
    record = AgentRecord(agent_id=agent_id, agent_name=payload.agent_name, cast_config=payload.cast_config)
    _agents[agent_id] = record
    return record


@app.get("/agents/{agent_id}", response_model=AgentRecord)
def get_agent(agent_id: str) -> AgentRecord:
    record = _agents.get(agent_id)
    if record is None:
        raise HTTPException(status_code=404, detail="agent not found")
    return record


@app.get("/agents", response_model=list[AgentRecord])
def list_agents() -> list[AgentRecord]:
    return list(_agents.values())


@app.delete("/agents/{agent_id}", status_code=204)
def delete_agent(agent_id: str) -> None:
    if agent_id not in _agents:
        raise HTTPException(status_code=404, detail="agent not found")
    _agents.pop(agent_id)
