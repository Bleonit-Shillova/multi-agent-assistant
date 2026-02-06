"""
Writer Agent
The "writer" that creates the final deliverable based on research.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agents.config import OPENAI_API_KEY, DEFAULT_MODEL
from agents.state import AgentState, AgentTrace


# Initialize the language model
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model=DEFAULT_MODEL,
    temperature=0.3  # Slightly creative for better writing
)

# The prompt for the Writer Agent
WRITER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a Writer Agent in a multi-agent research system.

Your job is to create polished, professional deliverables based on research notes.

CRITICAL RULES:
1. ONLY use information from the provided research notes
2. ALWAYS include citations in your output [Source: document name]
3. If research notes say "NOT FOUND", acknowledge the gap in your output
4. Write in a clear, professional tone
5. Structure your output appropriately for the requested format

For different output types:
- EMAIL: Professional email format with greeting, body, closing
- SUMMARY: Executive summary with bullet points and sections
- ACTION LIST: Clear tasks with owners and deadlines if available
- COMPARISON: Structured comparison with pros/cons and recommendation

Always end with a SOURCES section listing all documents referenced."""),
    ("human", """Original Request: {user_input}

Plan: {plan}

Research Notes:
{research_notes}

Create the final deliverable based on the plan and research. Include citations.""")
])


def format_research_notes(notes) -> str:
    """Format research notes into readable text."""
    if not notes:
        return "No research notes available."
    
    formatted = []
    for i, note in enumerate(notes, 1):
        formatted.append(f"""Note {i}:
- Finding: {note['content']}
- Source: {note['source']}
- Relevance: {note['relevance']}""")
    
    return "\n\n".join(formatted)


def run_writer(state: AgentState) -> dict:
    """
    Execute the Writer Agent.
    
    Creates the final deliverable from research notes.
    
    Args:
        state: Current shared state with research
        
    Returns:
        Updated state with draft
    """
    user_input = state.get("user_input", "")
    plan = state.get("plan", "")
    research_notes = state.get("research_notes", [])
    current_step = state.get("current_step", 0)
    
    # Format research notes for the prompt
    notes_text = format_research_notes(research_notes)
    
    # Generate the draft
    chain = WRITER_PROMPT | llm
    response = chain.invoke({
        "user_input": user_input,
        "plan": plan,
        "research_notes": notes_text
    })
    
    draft = response.content
    
    # Create trace entry
    trace_entry = AgentTrace(
        step=current_step + 1,
        agent="Writer",
        action="Generated draft deliverable",
        outcome=f"Created {len(draft)} character document"
    )
    
    return {
        "draft": draft,
        "trace": [trace_entry],
        "current_step": current_step + 1
    }