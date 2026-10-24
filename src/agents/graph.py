from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from src.agents.memory import (
    get_async_checkpointer,
    get_checkpointer,
    get_thread_config,
)
from src.agents.nodes import (
    defense_node,
    judge_node,
    prosecution_node,
    triage_node,
)
from src.agents.state import ConfessionState

# Node names
TRIAGE = "triage"
JUDGE = "judge"
DEFENSE = "defense"
PROSECUTION = "prosecution"

# Purchasable powers
POWER_LAWYER = "ai_lawyer"
POWER_PROSECUTOR = "ai_prosecutor"


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def _has_power(state: ConfessionState, power: str) -> bool:
    return power in (state.get("active_powers") or [])


def route_after_triage(state: ConfessionState) -> str:
    """Go to the judge if the confession is approved, otherwise stop."""
    return JUDGE if state.get("mod_status") == "approved" else END


def route_after_judge(state: ConfessionState) -> str:
    """Go to defense if active, else prosecution if active, else stop."""
    if _has_power(state, POWER_LAWYER):
        return DEFENSE
    if _has_power(state, POWER_PROSECUTOR):
        return PROSECUTION
    return END


def route_after_defense(state: ConfessionState) -> str:
    """Go to prosecution if active, else stop."""
    return PROSECUTION if _has_power(state, POWER_PROSECUTOR) else END


# ---------------------------------------------------------------------------
# Graph definition
# ---------------------------------------------------------------------------

workflow = StateGraph(ConfessionState)

workflow.add_node(TRIAGE, triage_node)
workflow.add_node(JUDGE, judge_node)
workflow.add_node(DEFENSE, defense_node)
workflow.add_node(PROSECUTION, prosecution_node)

workflow.add_edge(START, TRIAGE)
workflow.add_conditional_edges(TRIAGE, route_after_triage, {JUDGE: JUDGE, END: END})
workflow.add_conditional_edges(
    JUDGE, route_after_judge, {DEFENSE: DEFENSE, PROSECUTION: PROSECUTION, END: END}
)
workflow.add_conditional_edges(
    DEFENSE, route_after_defense, {PROSECUTION: PROSECUTION, END: END}
)
workflow.add_edge(PROSECUTION, END)

# Default graph backed by the in-memory checkpointer.
checkpointer = get_checkpointer()
graph_app = workflow.compile(checkpointer=checkpointer)


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------


def _build_initial_state(
    content: str,
    confession_id: int | str,
    active_powers: list[str],
) -> ConfessionState:
    return {
        "confession_id": confession_id,
        "content": content,
        "mod_status": "pending_ai",
        "severity": 0,
        "roast_allowed": True,
        "triage_reason": "",
        "ai_roast": None,
        "ai_defense": None,
        "ai_prosecution": None,
        "active_powers": active_powers,
        "guardrails_triggered": [],
        "messages": [HumanMessage(content=content)],
    }


async def run_confession_pipeline(
    content: str,
    confession_id: int | str,
    active_powers: list[str],
) -> dict[str, Any]:
    """Run the multi-agent pipeline for one confession, persisting state by thread."""
    initial_state = _build_initial_state(content, confession_id, active_powers)
    config = get_thread_config(confession_id)

    async with get_async_checkpointer() as saver:
        app = workflow.compile(checkpointer=saver)
        return await app.ainvoke(initial_state, config=config)


__all__ = [
    "route_after_triage",
    "route_after_judge",
    "route_after_defense",
    "workflow",
    "checkpointer",
    "graph_app",
    "run_confession_pipeline",
]