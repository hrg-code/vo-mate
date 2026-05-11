from __future__ import annotations

from app.agents.runtime.graph_runner import agent_graph_runner
from app.agents.runtime.state import ContentCreationState
from app.schemas.agent import AgentWorkbenchRequest, AgentWorkbenchResponse
from app.services.agent_store_service import agent_store


class AgentWorkbenchService:
    def run(self, request: AgentWorkbenchRequest) -> AgentWorkbenchResponse:
        run = agent_store.create_run(request.thread_id, "topic-workbench", request.model_dump(by_alias=True))
        initial_state: ContentCreationState = {
            "run_id": run.id,
            "thread_id": request.thread_id,
            "workspace_id": request.workspace_id,
            "member_id": request.member_id,
            "account_id": request.account_id,
            "request": request.model_dump(by_alias=True),
            "revision_count": 0,
            "errors": [],
        }

        try:
            final_state = agent_graph_runner.run_content_creation(initial_state)
            response = final_state["final_response"]
            if not isinstance(response, AgentWorkbenchResponse):
                response = AgentWorkbenchResponse(**response)
            agent_store.finish_run(run.id, response.model_dump(by_alias=True))
            return response
        except Exception as exc:
            agent_store.fail_run(run.id, f"{exc.__class__.__name__}: {exc}")
            raise


agent_workbench_service = AgentWorkbenchService()
