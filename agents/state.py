"""
Shared State Module
This defines the data structure that all agents share.
Think of it as a shared whiteboard where agents write their work.
"""

from typing import TypedDict, List, Optional, Annotated
from operator import add


class AgentTrace(TypedDict):
    """
    Record of a single agent action.
    This creates the trace/log table required by the project.
    """
    step: int
    agent: str
    action: str
    outcome: str


class ResearchNote(TypedDict):
    """
    A piece of research with its source citation.
    """
    content: str
    source: str
    relevance: str


class AgentState(TypedDict):
    """
    The shared state that all agents read from and write to.
    
    This is passed through the workflow:
    User Input → Planner → Researcher → Writer → Verifier → Final Output
    
    Each agent can see what previous agents did and add their own work.
    """
    
    # User's original request
    user_input: str
    
    # The plan created by the Planner Agent
    plan: Optional[str]
    plan_steps: Optional[List[str]]
    
    # Research notes gathered by the Research Agent
    research_notes: Optional[List[ResearchNote]]
    
    # Draft created by the Writer Agent
    draft: Optional[str]
    
    # Verification result from the Verifier Agent
    verification_result: Optional[str]
    verification_passed: Optional[bool]
    issues_found: Optional[List[str]]
    
    # Final output
    final_output: Optional[str]
    
    # Trace log - records what each agent did
    # The Annotated[List, add] means new entries are added to existing list
    trace: Annotated[List[AgentTrace], add]
    
    # Current step number
    current_step: int
    
    # Any errors that occurred
    errors: Optional[List[str]]