"""
LangGraph orchestration graph.
Defines the agent pipeline and state transitions.
"""
import logging
from typing import Literal
from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.hunter_agent import hunter_agent
from app.agents.synthesizer_agent import synthesizer_agent
from app.agents.perspective_agent import perspective_agent
from app.agents.connection_agent import connection_agent
from app.agents.tracker_agent import tracker_agent
from app.agents.feedback_processor_agent import feedback_processor_agent
from app.agents.output_formatter_agent import output_formatter_agent
from app.agents.delivery_agent import delivery_agent

logger = logging.getLogger(__name__)


def router(state: AgentState) -> Literal[
    "hunter_agent", "synthesizer_agent", "perspective_agent",
    "connection_agent", "tracker_agent", "feedback_processor_agent",
    "output_formatter_agent", "delivery_agent", END,
]:
    """Route to the next agent based on current_node in state."""
    return state.current_node


def build_news_graph() -> StateGraph:
    """Build and compile the LangGraph for the news pipeline."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("hunter_agent", hunter_agent)
    workflow.add_node("synthesizer_agent", synthesizer_agent)
    workflow.add_node("perspective_agent", perspective_agent)
    workflow.add_node("connection_agent", connection_agent)
    workflow.add_node("tracker_agent", tracker_agent)
    workflow.add_node("feedback_processor_agent", feedback_processor_agent)
    workflow.add_node("output_formatter_agent", output_formatter_agent)
    workflow.add_node("delivery_agent", delivery_agent)

    # Set entry point
    workflow.set_entry_point("hunter_agent")

    # Add edges with conditional routing
    workflow.add_conditional_edges("hunter_agent", router)
    workflow.add_conditional_edges("synthesizer_agent", router)
    workflow.add_conditional_edges("perspective_agent", router)
    workflow.add_conditional_edges("connection_agent", router)
    workflow.add_conditional_edges("tracker_agent", router)
    workflow.add_conditional_edges("feedback_processor_agent", router)
    workflow.add_conditional_edges("output_formatter_agent", router)

    # Delivery agent always ends
    workflow.add_conditional_edges("delivery_agent", router)

    return workflow.compile()


# Singleton graph
news_graph = build_news_graph()