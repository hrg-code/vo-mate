from fastapi import APIRouter

from app.api.v1 import agent, ai, analytics, auth, collector, contents, memory, scripts, system, workflows, workspaces

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(workspaces.router)
api_router.include_router(contents.router)
api_router.include_router(analytics.router)
api_router.include_router(ai.router)
api_router.include_router(scripts.router)
api_router.include_router(agent.router)
api_router.include_router(memory.router)
api_router.include_router(collector.router)
api_router.include_router(workflows.router)
api_router.include_router(system.router)
