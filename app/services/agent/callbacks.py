"""
LangChain Callback Handler for Astro AI

Centralised logging of every agent turn and tool call via LangChain's
BaseCallbackHandler. No logging code lives in individual tools — this
handler is notified automatically by the LangChain/LangGraph runtime.

Logs (what we capture):
  [AGENT]     turn N              — each time the LLM is invoked
  [TOOL CALL] <name> | <args>     — tool name + key arguments (no answer content)
  [TOOL DONE] <name> | <summary> | <ms>  — compact result summary + duration
  [TOOL ERROR] <name> | <ms> | <error>   — failures with traceback

Not logged: user questions, LLM answers, full tool payloads.
"""

import json
import time
from typing import Any, Dict, Optional
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from app.logger import get_logger

logger = get_logger("callbacks")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_tool_input(tool_name: str, args: Dict[str, Any]) -> str:
    """Produce a compact, readable summary of tool arguments."""
    parts: list[str] = []

    # Birth details — shared by generate_kundali_chart and get_vimshottari_dasha
    if all(k in args for k in ("day", "month", "year", "hour", "minute")):
        parts.append(
            f"birth={int(args['day']):02d}/{int(args['month']):02d}/{args['year']} "
            f"{int(args['hour']):02d}:{int(args['minute']):02d}"
        )
        if args.get("birth_place"):
            parts.append(f"place={args['birth_place']}")

    # Dasha date range
    if "start_date" in args:
        parts.append(f"range={args['start_date']} → {args.get('end_date', '?')}")

    # Knowledge base query
    if "query_type" in args:
        parts.append(f"type={args['query_type']}")
        for key in ("planet", "sign", "house", "nakshatra", "planet1", "planet2"):
            if args.get(key) is not None:
                parts.append(f"{key}={args[key]}")

    return " | ".join(parts) if parts else str(args)


def _summarise_output(tool_name: str, output: Any) -> str:
    """
    Extract a brief, content-free summary from a tool's output.
    Never logs the actual interpretation text or full chart data.
    """
    try:
        data = json.loads(output) if isinstance(output, str) else output

        if tool_name == "get_vimshottari_dasha" and isinstance(data, list):
            return f"{len(data)} period(s)"

        if tool_name == "generate_kundali_chart" and isinstance(data, dict):
            asc = data.get("ascendant_sign", "?")
            nak = data.get("nakshatra", "?")
            return f"ascendant={asc} nakshatra={nak}"

        if tool_name == "query_knowledge_base" and isinstance(data, dict):
            return "not found" if "error" in data else "OK"

    except Exception:
        pass

    return "done"


# ---------------------------------------------------------------------------
# Callback handler
# ---------------------------------------------------------------------------

class AstroLoggerCallback(BaseCallbackHandler):
    """
    LangChain callback handler that logs agent turns and tool calls.

    Create a fresh instance per agent invocation so the turn counter
    always starts at 1 for each user request.

    Usage:
        result = graph.invoke(state, config={"callbacks": [AstroLoggerCallback()]})
    """

    def __init__(self) -> None:
        super().__init__()
        self._turn: int = 0
        self._active_tools: Dict[str, Dict[str, Any]] = {}
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0

    # ------------------------------------------------------------------
    # LLM events  (fires each time the LLM is called inside the graph)
    # ------------------------------------------------------------------

    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: Any,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._turn += 1
        logger.info(f"[AGENT] turn {self._turn}")

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> None:
        usage = (response.llm_output or {}).get("token_usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        if input_tokens or output_tokens:
            logger.info(f"[AGENT] usage | turn={self._turn} in={input_tokens} out={output_tokens}")

    # ------------------------------------------------------------------
    # Tool events
    # ------------------------------------------------------------------

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        inputs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        tool_name = serialized.get("name", "unknown")

        # Record name and start time so on_tool_end can look them up
        self._active_tools[str(run_id)] = {
            "name": tool_name,
            "time": time.perf_counter(),
        }

        # Prefer the pre-parsed `inputs` dict; fall back to parsing input_str as JSON
        if inputs is not None:
            args = inputs
        else:
            try:
                args = json.loads(input_str)
            except Exception:
                args = {"raw": input_str}

        logger.info(f"[TOOL CALL] {tool_name} | {_format_tool_input(tool_name, args)}")

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        info = self._active_tools.pop(str(run_id), {})
        tool_name = info.get("name", "unknown")
        elapsed_ms = (time.perf_counter() - info["time"]) * 1000 if "time" in info else 0
        summary = _summarise_output(tool_name, output)
        logger.info(f"[TOOL DONE] {tool_name} | {summary} | {elapsed_ms:.0f}ms")

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        info = self._active_tools.pop(str(run_id), {})
        tool_name = info.get("name", "unknown")
        elapsed_ms = (time.perf_counter() - info["time"]) * 1000 if "time" in info else 0
        logger.error(
            f"[TOOL ERROR] {tool_name} | {elapsed_ms:.0f}ms | {error}",
            exc_info=True,
        )

    # ------------------------------------------------------------------
    # LLM error  (401, 429, 503, network timeout, etc.)
    # ------------------------------------------------------------------

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        # Try to surface the HTTP status code if LiteLLM / httpx attached one
        status = getattr(error, "status_code", None)
        status_str = f" | status={status}" if status else ""
        logger.error(
            f"[LLM ERROR] turn {self._turn}{status_str} | {type(error).__name__}: {error}",
            exc_info=True,
        )

    # ------------------------------------------------------------------
    # Chain / graph error  (catch-all for anything not covered above)
    # ------------------------------------------------------------------

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        logger.error(
            f"[CHAIN ERROR] {type(error).__name__}: {error}",
            exc_info=True,
        )
