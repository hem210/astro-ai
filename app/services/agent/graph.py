"""
LangGraph Agent Graph Definition

Defines the state schema and agent graph for the astrology agent.
"""

from typing import TypedDict, List, Optional, Dict, Any, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.language_models import BaseChatModel
from app.services.agent.config import SYSTEM_PROMPT

# Import add_messages reducer (LangGraph best practice for message lists)
try:
    from langgraph.graph.message import add_messages
except ImportError:
    # Fallback: define a simple reducer that appends messages
    def add_messages(left: List[BaseMessage], right: List[BaseMessage]) -> List[BaseMessage]:
        """Reducer function to merge message lists."""
        return left + right


class AgentState(TypedDict):
    """State schema for the astrology agent."""
    messages: Annotated[List[BaseMessage], add_messages]
    kundali_data: Optional[Dict[str, Any]]


def create_agent_graph(
    llm: BaseChatModel,
    tools: List
) -> StateGraph:
    """
    Create and compile the LangGraph agent graph.
    
    Args:
        llm: The language model to use (via LiteLLM)
        tools: List of tools available to the agent
    
    Returns:
        Compiled LangGraph graph
    """
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # Create tool node
    tool_node = ToolNode(tools)
    
    # Define agent node
    def agent_node(state: AgentState) -> AgentState:
        """Agent node that processes messages and decides on tool calls."""
        messages = state["messages"]
        
        # Check if system message is already at the beginning of the messages
        # Only add system message if it's not already present at the start
        has_system_message = messages and isinstance(messages[0], SystemMessage)
        
        # Prepare messages with system prompt
        if not has_system_message:
            # Add system message at the beginning
            messages_with_system = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        else:
            messages_with_system = messages
        
        # Invoke LLM with tools
        response = llm_with_tools.invoke(messages_with_system)
        
        # Return new message to be added to state (reducer will handle merging)
        return {"messages": [response]}
    
    # Define conditional edge function
    def should_continue(state: AgentState) -> str:
        """Determine whether to continue to tools or end."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If the last message has tool calls, continue to tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        # Otherwise, end
        return END
    
    # Build graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    
    # Add edge from tools back to agent
    workflow.add_edge("tools", "agent")
    
    # Compile graph
    return workflow.compile()


def extract_kundali_data(state: AgentState) -> Optional[Dict[str, Any]]:
    """
    Extract kundali data from tool messages in the state.
    
    Args:
        state: Current agent state
    
    Returns:
        Kundali data dictionary if found, None otherwise
    """
    messages = state.get("messages", [])
    
    for message in reversed(messages):
        if isinstance(message, ToolMessage):
            try:
                # Check if this is a kundali chart generation result
                if isinstance(message.content, dict) and "ascendant" in message.content:
                    return message.content
            except (AttributeError, TypeError):
                continue
    
    return None

