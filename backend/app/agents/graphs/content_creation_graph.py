from __future__ import annotations

from app.agents.nodes.compress_thread import compress_thread_memory
from app.agents.nodes.finalize import finalize_response
from app.agents.nodes.generate_script import generate_title_description_script
from app.agents.nodes.generate_strategy import generate_strategy
from app.agents.nodes.load_context import load_account_context
from app.agents.nodes.parse_request import parse_request
from app.agents.nodes.qa_content import qa_content
from app.agents.nodes.retrieve_memories import retrieve_memories
from app.agents.nodes.revise_content import revise_content
from app.agents.nodes.schedule_learning import schedule_memory_learning
from app.agents.nodes.score_topic import score_topic
from app.agents.policies.routing import route_after_qa
from app.agents.runtime.state import ContentCreationState


class SequentialContentCreationGraph:
    """Fallback runner for local environments without langgraph installed."""

    def invoke(self, initial_state: ContentCreationState) -> ContentCreationState:
        state = dict(initial_state)
        for node in (
            parse_request,
            load_account_context,
            retrieve_memories,
            score_topic,
            generate_strategy,
            generate_title_description_script,
            qa_content,
        ):
            state.update(node(state))

        while route_after_qa(state) == "revise_content":
            state.update(revise_content(state))
            state.update(qa_content(state))

        for node in (finalize_response, compress_thread_memory, schedule_memory_learning):
            state.update(node(state))
        return state


def build_content_creation_graph():
    try:
        from langgraph.graph import END, StateGraph
    except ModuleNotFoundError:
        return SequentialContentCreationGraph()

    graph = StateGraph(ContentCreationState)
    graph.add_node("parse_request", parse_request)
    graph.add_node("load_account_context", load_account_context)
    graph.add_node("retrieve_memories", retrieve_memories)
    graph.add_node("score_topic", score_topic)
    graph.add_node("generate_strategy", generate_strategy)
    graph.add_node("generate_title_description_script", generate_title_description_script)
    graph.add_node("qa_content", qa_content)
    graph.add_node("revise_content", revise_content)
    graph.add_node("finalize_response", finalize_response)
    graph.add_node("compress_thread_memory", compress_thread_memory)
    graph.add_node("schedule_memory_learning", schedule_memory_learning)

    graph.set_entry_point("parse_request")
    graph.add_edge("parse_request", "load_account_context")
    graph.add_edge("load_account_context", "retrieve_memories")
    graph.add_edge("retrieve_memories", "score_topic")
    graph.add_edge("score_topic", "generate_strategy")
    graph.add_edge("generate_strategy", "generate_title_description_script")
    graph.add_edge("generate_title_description_script", "qa_content")
    graph.add_conditional_edges(
        "qa_content",
        route_after_qa,
        {
            "revise_content": "revise_content",
            "finalize_response": "finalize_response",
        },
    )
    graph.add_edge("revise_content", "qa_content")
    graph.add_edge("finalize_response", "compress_thread_memory")
    graph.add_edge("compress_thread_memory", "schedule_memory_learning")
    graph.add_edge("schedule_memory_learning", END)
    return graph.compile()
