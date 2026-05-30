"""
WorkFlow — AI Service
======================
The intelligence layer of WorkFlow. Implements:

1. verifyLog()        — LangChain + Ollama: evaluate work log credibility
2. generateManagerSummary() — LangChain: plain-English team briefing
3. WorkflowAgent      — LangGraph agent: multi-step reasoning & task analysis
4. RAGService         — LlamaIndex + pgvector: semantic task history search

Architecture:
  LLMFactory → ChatOllama → LangChain chains → structured Pydantic output
  LlamaIndex VectorStore → pgvector → semantic search on work logs
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any, TypedDict

import structlog
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.llm_factory import LLMFactory
from app.schemas.work_log import LogVerificationResult
from app.models.work_log import AIConfidence

logger = structlog.get_logger()

# ─────────────────────────────────────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────────────────────────────────────

VERIFY_SYSTEM = """You are a workplace accountability assistant. Your job is to \
evaluate whether an employee's daily work log entry genuinely reflects real \
progress on their assigned task. Be fair but critical of vague, evasive, or \
off-topic entries."""

VERIFY_USER = """\
Task title: {title}
Task description: {description}

Employee's work log entry:
{log_text}

Evaluate this log entry. Respond ONLY with valid JSON in this exact format:
{{"confidence": "High" | "Medium" | "Low", "feedback": "one sentence explanation"}}

High = detailed and clearly relevant to the task.
Medium = partially relevant or somewhat vague.
Low = vague, off-topic, or looks like bluffing."""

SUMMARY_SYSTEM = """You are a productivity assistant helping a manager understand \
their team's current work status. Be concise, direct, and highlight risks and standouts."""

SUMMARY_USER = """\
Here is the current task list for my team:
{task_table}

Write a short plain-English briefing (max 5 sentences) covering:
1) who is behind or overdue
2) what is at risk of missing deadline
3) who is performing well
Do not list every task — synthesise."""

TRIAGE_SYSTEM = """You are WorkFlow's AI assistant. Given a task description, \
suggest an appropriate priority (low/medium/high/critical) and realistic deadline \
in ISO format. Return ONLY JSON: {{"priority": "...", "deadline_days": <int>, "reasoning": "..."}}"""


# ─────────────────────────────────────────────────────────────────────────────
# 1. Work-Log Verification
# ─────────────────────────────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
async def verifyLog(
    task_title: str,
    task_description: str | None,
    log_text: str,
) -> LogVerificationResult:
    """
    Uses Ollama (JSON mode) to evaluate an employee work log.
    Returns LogVerificationResult(confidence, feedback).
    Retries up to 3× on failure with exponential back-off.
    """
    llm = LLMFactory.get_json_llm()
    messages = [
        SystemMessage(content=VERIFY_SYSTEM),
        HumanMessage(
            content=VERIFY_USER.format(
                title=task_title,
                description=task_description or "No description provided.",
                log_text=log_text,
            )
        ),
    ]

    try:
        response = await llm.ainvoke(messages)
        raw = response.content if hasattr(response, "content") else str(response)

        # Attempt to extract JSON from the response
        data = _extract_json(raw)
        confidence_str = data.get("confidence", "Medium")
        feedback = data.get("feedback", "Unable to parse AI feedback.")

        # Normalise confidence to enum
        confidence_map = {"high": AIConfidence.HIGH, "medium": AIConfidence.MEDIUM, "low": AIConfidence.LOW}
        confidence = confidence_map.get(confidence_str.lower(), AIConfidence.MEDIUM)

        logger.info(
            "ai.verify_log",
            task=task_title,
            confidence=confidence,
        )
        return LogVerificationResult(confidence=confidence, feedback=feedback)

    except Exception as exc:
        logger.warning("ai.verify_log.failed", error=str(exc))
        return LogVerificationResult(
            confidence=AIConfidence.MEDIUM,
            feedback="Unable to verify — manual review recommended.",
        )


# ─────────────────────────────────────────────────────────────────────────────
# 2. Manager Summary ("Where's my team?")
# ─────────────────────────────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    reraise=True,
)
async def generateManagerSummary(tasks: list[dict[str, Any]]) -> str:
    """
    Generates a plain-English manager briefing from the task list.
    tasks: list of {title, assignedTo, priority, deadline, status}
    Returns: raw text string for the frontend to render.
    """
    if not tasks:
        return "No tasks are currently assigned. The team has a clean slate."

    now = datetime.now(timezone.utc)

    # Format task table
    rows = []
    for t in tasks:
        deadline = t.get("deadline", "")
        try:
            dl = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
            days_left = (dl - now).days
            deadline_label = f"{deadline[:10]} ({days_left:+d}d)"
        except Exception:
            deadline_label = deadline

        rows.append(
            f"• {t['title']} | assigned to {t.get('assignedTo', 'Unassigned')} "
            f"| {t.get('priority', 'medium').upper()} priority "
            f"| deadline {deadline_label} | status: {t.get('status', 'pending')}"
        )

    task_table = "\n".join(rows)

    llm = LLMFactory.get_chat_llm(temperature=0.3)
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(SUMMARY_SYSTEM),
        HumanMessagePromptTemplate.from_template(SUMMARY_USER),
    ])
    chain = prompt | llm | StrOutputParser()

    try:
        summary = await chain.ainvoke({"task_table": task_table})
        logger.info("ai.manager_summary.generated", task_count=len(tasks))
        return summary.strip()
    except Exception as exc:
        logger.warning("ai.manager_summary.failed", error=str(exc))
        return (
            "AI summary unavailable. Please check Ollama is running and "
            f"model '{LLMFactory._chat_model}' is loaded."
        )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Smart Task Triage (priority + deadline suggestion)
# ─────────────────────────────────────────────────────────────────────────────

async def suggestTaskPriority(title: str, description: str) -> dict[str, Any]:
    """
    Given a task title + description, suggest priority and deadline.
    Returns: {priority, deadline_days, reasoning}
    """
    llm = LLMFactory.get_json_llm()
    messages = [
        SystemMessage(content=TRIAGE_SYSTEM),
        HumanMessage(content=f"Task: {title}\nDescription: {description}"),
    ]
    try:
        response = await llm.ainvoke(messages)
        raw = response.content if hasattr(response, "content") else str(response)
        return _extract_json(raw)
    except Exception as exc:
        logger.warning("ai.triage.failed", error=str(exc))
        return {"priority": "medium", "deadline_days": 7, "reasoning": "Default suggestion"}


# ─────────────────────────────────────────────────────────────────────────────
# 4. LangGraph Agent — WorkFlow Accountability Agent
# ─────────────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    """State passed between LangGraph nodes."""
    messages: list[BaseMessage]
    task_context: dict[str, Any]
    analysis: str
    recommendations: list[str]
    risk_level: str  # low | medium | high | critical


def _build_accountability_graph() -> StateGraph:
    """
    LangGraph agent that runs multi-step analysis on a task batch.
    Steps: analyse_risks → flag_anomalies → generate_recommendations
    """
    llm = LLMFactory.get_chat_llm(temperature=0.2)

    async def analyse_risks(state: AgentState) -> AgentState:
        """Step 1: Identify risky tasks (overdue, high priority, no logs)."""
        tasks = state["task_context"].get("tasks", [])
        overdue = [t for t in tasks if t.get("status") == "overdue"]
        high_priority = [t for t in tasks if t.get("priority") in ("high", "critical")]
        no_logs = [t for t in tasks if t.get("log_count", 0) == 0]

        analysis = (
            f"Risk Analysis: {len(overdue)} overdue, "
            f"{len(high_priority)} high/critical priority, "
            f"{len(no_logs)} tasks with no work logs submitted."
        )
        state["analysis"] = analysis
        state["risk_level"] = "critical" if len(overdue) > 3 else ("high" if overdue else "medium")
        return state

    async def flag_anomalies(state: AgentState) -> AgentState:
        """Step 2: Use LLM to spot patterns (employees with all Low confidence)."""
        tasks = state["task_context"].get("tasks", [])
        low_conf_employees = {}
        for t in tasks:
            if t.get("latest_ai_confidence") == "Low":
                emp = t.get("assignedTo", "Unknown")
                low_conf_employees[emp] = low_conf_employees.get(emp, 0) + 1

        anomalies = [
            f"{emp} has {count} tasks flagged as Low confidence work logs"
            for emp, count in low_conf_employees.items()
            if count >= 2
        ]
        if anomalies:
            state["messages"].append(
                AIMessage(content=f"Anomalies detected: {'; '.join(anomalies)}")
            )
        return state

    async def generate_recommendations(state: AgentState) -> AgentState:
        """Step 3: LLM generates actionable recommendations."""
        context = f"""
Current situation: {state['analysis']}
Risk level: {state['risk_level']}
Anomalies: {[m.content for m in state['messages'] if isinstance(m, AIMessage)]}
"""
        messages = [
            SystemMessage(content="You are a workplace productivity coach. Give 3 specific, actionable recommendations."),
            HumanMessage(content=context),
        ]
        response = await llm.ainvoke(messages)
        recs = [line.strip() for line in response.content.split("\n") if line.strip() and line[0].isdigit()]
        state["recommendations"] = recs[:3] if recs else ["Review overdue tasks immediately."]
        return state

    graph = StateGraph(AgentState)
    graph.add_node("analyse_risks", analyse_risks)
    graph.add_node("flag_anomalies", flag_anomalies)
    graph.add_node("generate_recommendations", generate_recommendations)

    graph.add_edge(START, "analyse_risks")
    graph.add_edge("analyse_risks", "flag_anomalies")
    graph.add_edge("flag_anomalies", "generate_recommendations")
    graph.add_edge("generate_recommendations", END)

    return graph.compile()


# Singleton compiled graph
_accountability_agent = _build_accountability_graph()


async def runAccountabilityAgent(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Runs the LangGraph accountability agent on the full task list.
    Returns: {analysis, risk_level, recommendations}
    """
    initial_state: AgentState = {
        "messages": [],
        "task_context": {"tasks": tasks},
        "analysis": "",
        "recommendations": [],
        "risk_level": "low",
    }
    final_state = await _accountability_agent.ainvoke(initial_state)
    return {
        "analysis": final_state["analysis"],
        "risk_level": final_state["risk_level"],
        "recommendations": final_state["recommendations"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. RAG Service — Semantic Work Log Search (LlamaIndex + pgvector)
# ─────────────────────────────────────────────────────────────────────────────

class RAGService:
    """
    Semantic search over historical work logs using LlamaIndex.
    Embeddings: nomic-embed-text via Ollama
    Store: Supabase pgvector
    """

    _index: Any = None

    @classmethod
    async def initialize(cls, database_url: str) -> None:
        """Build or load the vector index. Called at app startup."""
        try:
            from llama_index.core import Settings as LISettings, VectorStoreIndex
            from llama_index.embeddings.ollama import OllamaEmbedding
            from llama_index.llms.ollama import Ollama as LIOllama
            from llama_index.vector_stores.supabase import SupabaseVectorStore

            from app.config import settings as app_settings

            # Configure LlamaIndex to use Ollama
            LISettings.llm = LIOllama(
                model=app_settings.ollama_model,
                base_url=app_settings.ollama_base_url,
            )
            LISettings.embed_model = OllamaEmbedding(
                model_name=app_settings.ollama_embedding_model,
                base_url=app_settings.ollama_base_url,
            )

            vector_store = SupabaseVectorStore(
                postgres_connection_string=database_url,
                collection_name="work_log_embeddings",
                dimension=768,
            )
            cls._index = VectorStoreIndex.from_vector_store(vector_store)
            logger.info("rag.initialized", store="supabase_pgvector")
        except Exception as exc:
            logger.warning("rag.init_failed", error=str(exc))

    @classmethod
    async def search_similar_logs(
        cls,
        query: str,
        task_id: uuid.UUID | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Find semantically similar work logs to the query."""
        if cls._index is None:
            return []
        try:
            engine = cls._index.as_query_engine(similarity_top_k=top_k)
            response = await engine.aquery(query)
            results = []
            for node in response.source_nodes:
                results.append({
                    "text": node.text,
                    "score": node.score,
                    "metadata": node.metadata,
                })
            return results
        except Exception as exc:
            logger.warning("rag.search_failed", error=str(exc))
            return []

    @classmethod
    async def index_log(cls, log_text: str, metadata: dict[str, Any]) -> None:
        """Add a new work log to the vector index."""
        if cls._index is None:
            return
        try:
            from llama_index.core import Document
            doc = Document(text=log_text, metadata=metadata)
            cls._index.insert(doc)
        except Exception as exc:
            logger.warning("rag.index_failed", error=str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────

def _extract_json(raw: str) -> dict[str, Any]:
    """
    Robustly extract JSON from LLM output.
    Handles markdown code fences, inline JSON, and partial wrapping.
    """
    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try extracting from ```json ... ``` blocks
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try extracting first { ... } block
    match = re.search(r"\{.*?\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Cannot extract JSON from LLM output: {raw[:200]}")
