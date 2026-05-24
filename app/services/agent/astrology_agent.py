"""
Astrology Agent

Main agent class that initializes and manages the LangGraph agent
for astrological queries.
"""

from typing import Optional, List
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_litellm import ChatLiteLLM
from app.services.agent.config import (
    get_model_config,
    AGENT_MODEL,
    validate_model_config
)
from app.services.agent.graph import create_agent_graph, AgentState
from app.services.agent.tools import generate_kundali_chart, query_knowledge_base, get_vimshottari_dasha
from app.services.agent.callbacks import AstroLoggerCallback
from app.logger import get_logger, setup_logging

logger = get_logger("agent")


class AstrologyAgent:
    """Main astrology agent class."""

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the astrology agent.

        Args:
            model_name: Name of the model to use (defaults to AGENT_MODEL env var)
        """
        # Initialise logging (no-op if already set up)
        setup_logging()

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
        self.tools = [generate_kundali_chart, query_knowledge_base, get_vimshottari_dasha]

        # Create and compile graph
        self.graph = create_agent_graph(self.llm, self.tools)
        logger.info(f"[AGENT] initialised | model={self.model_name}")

    def _build_messages(self, query: str, conversation_history: Optional[List]) -> List:
        """
        Assemble the message list from history + current query.
        Strips ToolMessages and AIMessages with tool_calls — only clean
        HumanMessage / final AIMessage pairs are carried across turns.
        """
        messages = []

        if conversation_history:
            for msg in conversation_history:
                if isinstance(msg, ToolMessage):
                    continue
                if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                    continue
                messages.append(msg)

        messages.append(HumanMessage(content=query))
        return messages

    def invoke(self, query: str, conversation_history: Optional[List] = None) -> str:
        """
        Invoke the agent with a query.

        Args:
            query: User query string
            conversation_history: Optional list of previous messages

        Returns:
            Agent response string
        """
        messages = self._build_messages(query, conversation_history)

        initial_state: AgentState = {
            "messages": messages,
            "kundali_data": None,
        }

        # A fresh callback instance per invocation keeps the turn counter accurate
        result = self.graph.invoke(
            initial_state,
            config={"callbacks": [AstroLoggerCallback()]},
        )

        # Extract final response
        final_messages = result.get("messages", [])

        # Find the last AI message that doesn't have pending tool calls
        for message in reversed(final_messages):
            if isinstance(message, AIMessage):
                if not getattr(message, "tool_calls", None):
                    return message.content

        # Fallback: return last AI message even if it has tool calls
        for message in reversed(final_messages):
            if isinstance(message, AIMessage):
                return message.content

        if final_messages:
            return str(final_messages[-1].content)

        return "I apologize, but I couldn't generate a response. Please try again."

    def stream(self, query: str, conversation_history: Optional[List] = None):
        """
        Stream agent responses.

        Args:
            query: User query string
            conversation_history: Optional list of previous messages

        Yields:
            Response chunks
        """
        messages = self._build_messages(query, conversation_history)

        initial_state: AgentState = {
            "messages": messages,
            "kundali_data": None,
        }

        for chunk in self.graph.stream(
            initial_state,
            config={"callbacks": [AstroLoggerCallback()]},
        ):
            yield chunk
