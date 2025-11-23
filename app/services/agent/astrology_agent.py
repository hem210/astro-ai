"""
Astrology Agent

Main agent class that initializes and manages the LangGraph agent
for astrological queries.
"""

from typing import Optional, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_litellm import ChatLiteLLM
from app.services.agent.config import (
    get_model_config,
    AGENT_MODEL,
    validate_model_config
)
from app.services.agent.graph import create_agent_graph, AgentState
from app.services.agent.tools import generate_kundali_chart, query_knowledge_base


class AstrologyAgent:
    """Main astrology agent class."""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the astrology agent.
        
        Args:
            model_name: Name of the model to use (defaults to AGENT_MODEL env var)
        """
        # Validate configuration
        validate_model_config()
        
        # Get model configuration (reads from env - fast)
        self.model_name = model_name or AGENT_MODEL
        model_config = get_model_config(self.model_name)
        
        # Create ChatLiteLLM instance (lightweight - no need to cache)
        # This handles all message conversion and tool calling automatically
        self.llm = ChatLiteLLM(
            model=model_config["litellm_model"],
            api_key=model_config["api_key"]
        )
        
        # Get tools
        self.tools = [generate_kundali_chart, query_knowledge_base]
        
        # Create and compile graph
        self.graph = create_agent_graph(self.llm, self.tools)
    
    def invoke(self, query: str, conversation_history: Optional[List] = None) -> str:
        """
        Invoke the agent with a query.
        
        Args:
            query: User query string
            conversation_history: Optional list of previous messages (should not include ToolMessages)
        
        Returns:
            Agent response string
        """
        # Build initial state
        messages = []
        
        # Add conversation history if provided
        # Filter out ToolMessages and AIMessages with tool_calls to avoid "missing tool call" errors
        # Only keep the final AIMessage responses (without tool_calls) which already incorporate tool results
        if conversation_history:
            from langchain_core.messages import ToolMessage
            for msg in conversation_history:
                # Skip ToolMessages - they're not needed between turns
                if isinstance(msg, ToolMessage):
                    continue
                # Skip AIMessages with tool_calls - we only want final responses
                if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                    continue
                # Include HumanMessage and final AIMessage (without tool_calls)
                messages.append(msg)
        
        # Add current query
        messages.append(HumanMessage(content=query))
        
        # Create initial state
        initial_state: AgentState = {
            "messages": messages,
            "kundali_data": None
        }
        
        # Invoke graph
        result = self.graph.invoke(initial_state)
        
        # Extract final response
        final_messages = result.get("messages", [])
        
        # Find the last AI message (that doesn't have tool calls)
        for message in reversed(final_messages):
            if isinstance(message, AIMessage):
                # Skip AIMessages with tool calls - we want the final response
                if not (hasattr(message, "tool_calls") and message.tool_calls):
                    return message.content
        
        # Fallback: return last AI message even if it has tool calls
        for message in reversed(final_messages):
            if isinstance(message, AIMessage):
                return message.content
        
        # Final fallback
        if final_messages:
            return str(final_messages[-1].content)
        
        return "I apologize, but I couldn't generate a response. Please try again."
    
    def stream(self, query: str, conversation_history: Optional[List] = None):
        """
        Stream agent responses.
        
        Args:
            query: User query string
            conversation_history: Optional list of previous messages (should not include ToolMessages)
        
        Yields:
            Response chunks
        """
        # Build initial state
        messages = []
        
        # Add conversation history if provided
        # Filter out ToolMessages and AIMessages with tool_calls to avoid "missing tool call" errors
        # Only keep the final AIMessage responses (without tool_calls) which already incorporate tool results
        if conversation_history:
            from langchain_core.messages import ToolMessage
            for msg in conversation_history:
                # Skip ToolMessages - they're not needed between turns
                if isinstance(msg, ToolMessage):
                    continue
                # Skip AIMessages with tool_calls - we only want final responses
                if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                    continue
                # Include HumanMessage and final AIMessage (without tool_calls)
                messages.append(msg)
        
        messages.append(HumanMessage(content=query))
        
        initial_state: AgentState = {
            "messages": messages,
            "kundali_data": None
        }
        
        # Stream from graph
        for chunk in self.graph.stream(initial_state):
            yield chunk

