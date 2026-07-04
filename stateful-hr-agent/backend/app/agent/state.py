from typing import Annotated, TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Core conversation state
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Custom memory state
    selected_candidate: Optional[str]
    current_workflow: Optional[str]
    last_ui: Optional[Dict[str, Any]]
    
    # Internal agent processing state
    intent: Optional[str]
    entities: Optional[Dict[str, Any]]
    required_tools: Optional[List[str]]
    plan: Optional[List[Dict[str, Any]]]
    mcp_results: Optional[List[Dict[str, Any]]]
    final_response: Optional[str]
    visible_context: Optional[List[Dict[str, Any]]]
    agent_trace_log: Optional[str]
