"""
Research Agent
The "researcher" that searches documents and gathers ATOMIC facts with citations.
Token-safe: limits context to avoid context_length_exceeded.
"""

from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agents.config import OPENAI_API_KEY, DEFAULT_MODEL
from agents.state import AgentState, AgentTrace, ResearchNote
from agents.document_loader import DocumentLoader


llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model=DEFAULT_MODEL,
    temperature=0
)

doc_loader = DocumentLoader()

RESEARCHER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a Research Agent in a multi-agent research system.

You must EXTRACT ATOMIC FACTS verbatim from documents.

ABSOLUTE RULES:
1) Use ONLY provided document excerpts.
2) DO NOT summarize or paraphrase list items.
3) DO NOT invent or label items (no "Item 1", "Request A", etc.).
4) ONE factual item = ONE research note.
5) ALWAYS cite the exact document filename.
6) If an item does not exist, explicitly write:
   FINDING: <item> NOT FOUND IN SOURCES
   SOURCE: <filename>
7) If a question asks for "top N" and a ranked/priority list exists, extract the first N items.

OUTPUT FORMAT (repeat as needed):

FINDING: <exact text from document OR NOT FOUND IN SOURCES>
SOURCE: <filename> — "<exact supporting snippet>"
RELEVANCE: <what question this fact answers>
"""),
    ("human", """RESEARCH PLAN:
{plan}

QUESTION BLOCKS WITH DOCUMENT EXCERPTS:
{context}

Extract ALL relevant atomic facts exactly as written.""")
])


def _preferred_filename_terms(q_lower: str) -> list[str]:
    terms = []
    if "project document" in q_lower or "project report" in q_lower or "project risk" in q_lower or "risk" in q_lower:
        terms += ["project_report.md", "key risks", "risks", "integration risk", "security risk", "resource risk", "budget risk", "timeline risk"]
    if "weekly update" in q_lower or "this week" in q_lower or "next week" in q_lower:
        terms += ["weekly_update.md", "progress this week", "next week plans"]
    if "competitor" in q_lower or "competitive" in q_lower:
        terms += ["competitor_analysis.md", "competitors", "pricing", "positioning", "strengths", "weaknesses"]
    if "client feedback" in q_lower or "improvement request" in q_lower or "success metrics" in q_lower:
        terms += ["client_feedback.md", "feature requests", "priority order", "metrics", "success", "user adoption rate", "daily active users", "session duration", "support tickets", "client success metrics"]
    if "q1 roadmap" in q_lower or "roadmap" in q_lower:
        terms += ["q1_roadmap.md", "milestones", "planned", "in progress"]
    if "technical" in q_lower or "architecture" in q_lower or "security" in q_lower or "performance" in q_lower or "system architecture" in q_lower:
        terms += ["technical_specs.md", "frontend", "backend", "infrastructure", "requirements", "React", "Node.js", "PostgreSQL", "API Response Time", "OAuth", "encryption"]
    if "meeting notes" in q_lower or "action item" in q_lower:
        terms += ["meeting_notes.md", "action items"]
    return terms


def _retrieval_k_for_question(q_lower: str) -> int:
    """
    Use fewer chunks for broad questions that otherwise blow context window.
    """
    if any(k in q_lower for k in ["competitor", "competitive position", "recommended strategy"]):
        return 7
    if any(k in q_lower for k in ["architecture", "infrastructure", "performance", "security requirements"]):
        return 8
    # default
    return 12


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"


def run_researcher(state: AgentState) -> dict:
    plan = state.get("plan", "")
    plan_steps = state.get("plan_steps", []) or []
    current_step = state.get("current_step", 0)

    base_retriever = doc_loader.get_retriever(k=20)  # we will self-limit per question
    if base_retriever is None:
        return {
            "research_notes": [],
            "trace": [AgentTrace(
                step=current_step + 1,
                agent="Researcher",
                action="Attempted document search",
                outcome="ERROR: No documents loaded"
            )],
            "current_step": current_step + 1,
            "errors": ["No documents found"]
        }

    questions = plan_steps or ([plan] if plan else [])
    context_blocks = []
    total_chunks = 0

    # Hard caps to prevent context blowups
    MAX_CHARS_PER_DOC = 900     # each chunk trimmed
    MAX_DOCS_PER_QUESTION = 8   # absolute upper bound even if k asks for more

    for q in questions:
        q_lower = q.lower()

        # Query expansion for better recall + source targeting
        extra_terms = []
        if "client feedback" in q_lower or "improvement" in q_lower or "metrics" in q_lower:
            extra_terms += ["feature requests", "priority", "improvement", "feedback", "metrics", "success metrics", "adoption rate", "daily active users"]
        if "competitor" in q_lower or "competitive" in q_lower or "strategy" in q_lower:
            extra_terms += ["competitor", "pricing", "positioning", "strength", "weakness", "recommendations"]
        if "risk" in q_lower:
            extra_terms += ["risk", "mitigation", "issue", "blocker"]

        extra_terms += _preferred_filename_terms(q_lower)

        expanded_query = q + "\n" + " ".join(extra_terms)

        # Per-question k (prevents Test 5 / 7 overflow)
        k = _retrieval_k_for_question(q_lower)
        docs = base_retriever.invoke(expanded_query)

        # manual cap: keep top-k AND enforce absolute cap
        docs = docs[:min(k, MAX_DOCS_PER_QUESTION)]

        total_chunks += len(docs)

        parts = []
        for doc in docs:
            source = doc.metadata.get("source", "Unknown")
            filename = source.split("/")[-1]
            content = _truncate(doc.page_content.strip(), MAX_CHARS_PER_DOC)
            parts.append(f"[Document: {filename}]\n{content}")

        context_blocks.append(f"QUESTION: {q}\n\n" + "\n---\n".join(parts))

    context = "\n\n" + ("=" * 70 + "\n\n").join(context_blocks)

    chain = RESEARCHER_PROMPT | llm
    response = chain.invoke({"plan": plan, "context": context})

    research_notes: List[ResearchNote] = []
    current = {}

    for line in response.content.splitlines():
        line = line.strip()

        if line.startswith("FINDING:"):
            if current:
                research_notes.append(ResearchNote(
                    content=current.get("finding", "").strip(),
                    source=current.get("source", "").strip(),
                    relevance=current.get("relevance", "").strip()
                ))
            current = {"finding": line.replace("FINDING:", "").strip()}

        elif line.startswith("SOURCE:"):
            current["source"] = line.replace("SOURCE:", "").strip()

        elif line.startswith("RELEVANCE:"):
            current["relevance"] = line.replace("RELEVANCE:", "").strip()

    if current:
        research_notes.append(ResearchNote(
            content=current.get("finding", "").strip(),
            source=current.get("source", "").strip(),
            relevance=current.get("relevance", "").strip()
        ))

    trace_entry = AgentTrace(
        step=current_step + 1,
        agent="Researcher",
        action="Extracted atomic research facts (token-safe)",
        outcome=f"{len(research_notes)} facts from {total_chunks} chunks"
    )

    return {
        "research_notes": research_notes,
        "trace": [trace_entry],
        "current_step": current_step + 1
    }