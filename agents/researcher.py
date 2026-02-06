"""
Research Agent
The "researcher" that searches documents and gathers information with citations.
"""

from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agents.config import OPENAI_API_KEY, DEFAULT_MODEL
from agents.state import AgentState, AgentTrace, ResearchNote
from agents.document_loader import DocumentLoader


# Initialize the language model
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model=DEFAULT_MODEL,
    temperature=0
)

# Initialize document loader
doc_loader = DocumentLoader()

# The prompt for the Research Agent
RESEARCHER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a Research Agent in a multi-agent system.

Your job is to find relevant information from documents to answer research questions.

CRITICAL RULES:
1. ONLY use information from the provided document excerpts
2. ALWAYS cite your sources with the document name
3. If information is NOT in the documents, say "NOT FOUND IN SOURCES"
4. Do NOT make up or invent any facts
5. Quote relevant passages when possible

For each piece of information you find, format it as:
FINDING: [The information you found]
SOURCE: [Document name and relevant quote]
RELEVANCE: [Why this is relevant to the question]

If you cannot find information for a question, respond with:
FINDING: Information not found
SOURCE: N/A
RELEVANCE: This information is not present in the provided documents"""),
    ("human", """Research Plan:
{plan}

Research Questions from the plan - find answers in these document excerpts:

DOCUMENT EXCERPTS:
{context}

Provide research notes for each question in the plan. Remember to cite sources!""")
])


def run_researcher(state: AgentState) -> dict:
    """
    Execute the Research Agent.
    
    Searches documents based on the plan and returns cited research notes.
    
    Args:
        state: Current shared state with plan
        
    Returns:
        Updated state with research notes
    """
    plan = state.get("plan", "")
    plan_steps = state.get("plan_steps", [])
    current_step = state.get("current_step", 0)
    
    # Get the document retriever
    retriever = doc_loader.get_retriever(k=6)  # Get top 6 relevant chunks
    
    if retriever is None:
        return {
            "research_notes": [],
            "trace": [AgentTrace(
                step=current_step + 1,
                agent="Researcher",
                action="Attempted document search",
                outcome="ERROR: No documents loaded. Please add documents to /data folder."
            )],
            "current_step": current_step + 1,
            "errors": ["No documents found in /data folder"]
        }
    
    # Search for relevant documents based on the plan
    # Combine plan and steps into a search query
    search_query = f"{plan}\n" + "\n".join(plan_steps)
    
    # Retrieve relevant document chunks
    docs = retriever.invoke(search_query)
    
    # Format the context from retrieved documents
    context_parts = []
    for i, doc in enumerate(docs):
        source = doc.metadata.get('source', 'Unknown')
        # Get just the filename
        source_name = source.split('/')[-1] if '/' in source else source
        context_parts.append(f"[Document: {source_name}]\n{doc.page_content}\n")
    
    context = "\n---\n".join(context_parts)
    
    # Run the research
    chain = RESEARCHER_PROMPT | llm
    response = chain.invoke({
        "plan": plan,
        "context": context
    })
    
    research_text = response.content
    
    # Parse the findings into structured notes
    research_notes = []
    current_finding = {}
    
    for line in research_text.split('\n'):
        line = line.strip()
        if line.startswith('FINDING:'):
            if current_finding:
                research_notes.append(ResearchNote(
                    content=current_finding.get('finding', ''),
                    source=current_finding.get('source', 'Not cited'),
                    relevance=current_finding.get('relevance', '')
                ))
            current_finding = {'finding': line[8:].strip()}
        elif line.startswith('SOURCE:'):
            current_finding['source'] = line[7:].strip()
        elif line.startswith('RELEVANCE:'):
            current_finding['relevance'] = line[10:].strip()
    
    # Don't forget the last finding
    if current_finding:
        research_notes.append(ResearchNote(
            content=current_finding.get('finding', ''),
            source=current_finding.get('source', 'Not cited'),
            relevance=current_finding.get('relevance', '')
        ))
    
    # Create trace entry
    trace_entry = AgentTrace(
        step=current_step + 1,
        agent="Researcher",
        action=f"Searched {len(docs)} document chunks",
        outcome=f"Found {len(research_notes)} relevant findings"
    )
    
    return {
        "research_notes": research_notes,
        "trace": [trace_entry],
        "current_step": current_step + 1
    }