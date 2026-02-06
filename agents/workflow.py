"""
Workflow Orchestration using LangGraph
This connects all agents into a coordinated workflow.
"""

from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.planner import run_planner
from agents.researcher import run_researcher
from agents.writer import run_writer
from agents.verifier import run_verifier


def create_workflow():
    """
    Create the multi-agent workflow graph.
    
    The flow is:
    START → Planner → Researcher → Writer → Verifier → END
    
    Returns:
        Compiled LangGraph workflow
    """
    
    # Create the graph with our state type
    workflow = StateGraph(AgentState)
    
    # Add nodes (each node is an agent)
    workflow.add_node("planner", run_planner)
    workflow.add_node("researcher", run_researcher)
    workflow.add_node("writer", run_writer)
    workflow.add_node("verifier", run_verifier)
    
    # Define the edges (how agents connect)
    # Start → Planner
    workflow.set_entry_point("planner")
    
    # Planner → Researcher
    workflow.add_edge("planner", "researcher")
    
    # Researcher → Writer
    workflow.add_edge("researcher", "writer")
    
    # Writer → Verifier
    workflow.add_edge("writer", "verifier")
    
    # Verifier → END
    workflow.add_edge("verifier", END)
    
    # Compile the workflow
    app = workflow.compile()
    
    return app


def run_assistant(user_input: str) -> dict:
    """
    Run the full multi-agent assistant.
    
    Args:
        user_input: The user's request
        
    Returns:
        Complete state with all results
    """
    # Create the workflow
    workflow = create_workflow()
    
    # Initialize state
    initial_state = {
        "user_input": user_input,
        "plan": None,
        "plan_steps": None,
        "research_notes": None,
        "draft": None,
        "verification_result": None,
        "verification_passed": None,
        "issues_found": None,
        "final_output": None,
        "trace": [],
        "current_step": 0,
        "errors": None
    }
    
    # Run the workflow
    final_state = workflow.invoke(initial_state)
    
    return final_state


def format_trace_table(trace: list) -> str:
    """
    Format the trace into a readable table.
    
    Args:
        trace: List of AgentTrace entries
        
    Returns:
        Formatted table string
    """
    if not trace:
        return "No trace entries."
    
    # Header
    table = "| Step | Agent | Action | Outcome |\n"
    table += "|------|-------|--------|--------|\n"
    
    # Rows
    for entry in trace:
        table += f"| {entry['step']} | {entry['agent']} | {entry['action']} | {entry['outcome']} |\n"
    
    return table