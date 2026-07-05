from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes import (
    input_node,
    intent_detection,
    memory_retrieval,
    planning_node,
    mcp_execution,
    ag_ui_generation,
    response_node
)

# Define the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("input", input_node)
workflow.add_node("intent_detection", intent_detection)
workflow.add_node("memory_retrieval", memory_retrieval)
workflow.add_node("planning", planning_node)
workflow.add_node("mcp_execution", mcp_execution)
workflow.add_node("ag_ui_generation", ag_ui_generation)
workflow.add_node("response", response_node)

# Add edges (Linear pipeline as requested)
workflow.set_entry_point("input")
workflow.add_edge("input", "intent_detection")
workflow.add_edge("intent_detection", "memory_retrieval")
workflow.add_edge("memory_retrieval", "planning")
workflow.add_edge("planning", "mcp_execution")
workflow.add_edge("mcp_execution", "ag_ui_generation")
workflow.add_edge("ag_ui_generation", "response")
workflow.add_edge("response", END)

# Compile graph; durable state is handled at API layer via DB persistence.
hr_agent_app = workflow.compile()
