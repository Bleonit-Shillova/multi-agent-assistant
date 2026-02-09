"""
Writer Agent
The "writer" that creates the final deliverable based on research.
"""
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agents.config import OPENAI_API_KEY, DEFAULT_MODEL
from agents.state import AgentState, AgentTrace


# Deterministic writing (no placeholders, no invention)
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model=DEFAULT_MODEL,
    temperature=0
)

WRITER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a Writer Agent in a multi-agent research system.

You must produce a final deliverable STRICTLY from the provided research notes.

ABSOLUTE RULES (violating any = FAIL):
1) Use ONLY facts present in the research notes.
2) Every factual sentence, bullet, numbered item, or sub-bullet MUST include a citation using EXACTLY this format: [Source: filename].
   - Always use singular [Source: filename], NEVER [Sources: filename].
3) Never use placeholder/template text of any kind.
   - The ONLY square brackets allowed are citations: [Source: filename]
   - NEVER write [Your Name], [Client], [Company Name], [Date], [Recipient], [Team], or ANY other bracketed placeholder.
   - For emails: use "Dear Team," or "Hello," as the greeting. End with "Best regards" and NOTHING after it. No name, no signature block.
4) If a research note says "NOT FOUND IN SOURCES":
   - You MUST repeat exactly "NOT FOUND IN SOURCES"
   - You MUST include a citation to the document checked
   - You MUST add ONE short sentence suggesting what type of document or data source might contain this information
     Example: NOT FOUND IN SOURCES. [Source: client_feedback.md] (This information might be found in a dedicated KPI dashboard or quarterly metrics report.)
5) Do not invent names, dates, metrics, tasks, milestones, owners, or interpretations.
6) Do NOT add explanations for why something is missing beyond the single suggestion sentence in rule 4.
7) Do NOT attempt to satisfy verifier wording — only restate research notes.

FORMAT RULES:
- Extraction / lists: EACH item must end with a citation.
- Multi-field items: EACH field line must have its own citation.
- Analysis/comparison: ONLY restate documented facts and derived conclusions explicitly supported by notes.
- Include a SOURCES section listing unique filenames IF at least one factual claim exists.
- If the entire output is only NOT FOUND IN SOURCES statements, do NOT include a SOURCES section.

You are not allowed to fix gaps. You are only allowed to report facts.
"""),
    ("human", """ORIGINAL REQUEST:
{user_input}

PLAN:
{plan}

RESEARCH NOTES (facts you may use):
{research_notes}

Write the deliverable now. Do not add anything not present in the research notes.""")
])


def format_research_notes(notes) -> str:
    if not notes:
        return "NO RESEARCH NOTES PROVIDED."

    formatted = []
    for i, note in enumerate(notes, 1):
        formatted.append(
            f"FACT {i}:\n"
            f"- CONTENT: {note.get('content','')}\n"
            f"- SOURCE: {note.get('source','')}\n"
            f"- RELEVANCE: {note.get('relevance','')}"
        )
    return "\n\n".join(formatted)


def _strip_placeholders(text: str) -> str:
    """
    Code-level safety net: remove ANY bracketed text that is NOT a valid
    [Source: ...] citation.  The LLM sometimes ignores prompt rules and
    still produces [Your Name], [Client], [Date], etc.
    """
    def _replace(match):
        content = match.group(0)
        # Keep valid citations like [Source: filename.md]
        if re.match(r"\[\s*Source\s*:", content, re.IGNORECASE):
            return content
        # Remove everything else
        return ""

    result = re.sub(r"\[[^\]]+\]", _replace, text)
    # Clean up leftover double-spaces and trailing whitespace
    result = re.sub(r"  +", " ", result)
    result = re.sub(r" +\n", "\n", result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def run_writer(state: AgentState) -> dict:
    user_input = state.get("user_input", "")
    plan = state.get("plan", "")
    research_notes = state.get("research_notes", []) or []
    current_step = state.get("current_step", 0)

    notes_text = format_research_notes(research_notes)

    chain = WRITER_PROMPT | llm
    response = chain.invoke({
        "user_input": user_input,
        "plan": plan,
        "research_notes": notes_text
    })

    draft = response.content.strip()

    # >>> FIX: strip any placeholder brackets the LLM still produced <<<
    draft = _strip_placeholders(draft)

    # If output contains ONLY NOT FOUND statements, remove trailing SOURCES section
    only_not_found = all(
        "not found in sources" in note.get("content", "").lower()
        for note in research_notes
    )

    if only_not_found:
        draft = re.sub(r"\n*\*\*sources\*\*.*$", "", draft, flags=re.IGNORECASE | re.DOTALL).strip()
        draft = re.sub(r"\n*SOURCES:.*$", "", draft, flags=re.IGNORECASE | re.DOTALL).strip()

    trace_entry = AgentTrace(
        step=current_step + 1,
        agent="Writer",
        action="Generated grounded draft deliverable",
        outcome=f"Created {len(draft)} character document"
    )

    return {
        "draft": draft,
        "trace": [trace_entry],
        "current_step": current_step + 1
    }