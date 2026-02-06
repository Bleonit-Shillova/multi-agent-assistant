"""
Planner Agent
The "manager" that breaks down user requests into actionable steps.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agents.config import OPENAI_API_KEY, DEFAULT_MODEL
from agents.state import AgentState, AgentTrace


# Initialize the language model
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model=DEFAULT_MODEL,
    temperature=0  # 0 = more deterministic responses
)

# The prompt that tells the Planner how to behave
PLANNER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a Planning Agent in a multi-agent research system.

Your job is to analyze user requests and create a clear, step-by-step plan.

For each request, you must:
1. Understand what the user wants
2. Break it into specific, actionable steps
3. Identify what information needs to be researched
4. Determine the final output format needed

Output your plan in this exact format:

GOAL: [One sentence describing the main objective]

STEPS:
1. [First research step]
2. [Second research step]
3. ...

OUTPUT FORMAT: [What the final deliverable should be - email, summary, action list, etc.]

RESEARCH QUESTIONS:
- [Question 1 to find in documents]
- [Question 2 to find in documents]
- ...

Be specific and actionable. Each step should be something the Research Agent can actually do."""),
    ("human", "{user_input}")
])


def run_planner(state: AgentState) -> dict:
    """
    Execute the Planner Agent.
    
    Takes the user's input and creates a structured plan.
    
    Args:
        state: Current shared state
        
    Returns:
        Updated state with plan added
    """
    user_input = state["user_input"]
    current_step = state.get("current_step", 0)
    
    # Create the prompt and get response
    chain = PLANNER_PROMPT | llm
    response = chain.invoke({"user_input": user_input})
    
    plan_text = response.content
    
    # Extract steps from the plan (simple parsing)
    steps = []
    lines = plan_text.split('\n')
    in_steps = False
    for line in lines:
        if line.strip().startswith('STEPS:'):
            in_steps = True
            continue
        if in_steps and line.strip() and line.strip()[0].isdigit():
            # Remove the number and period at the start
            step = line.strip()
            if '. ' in step:
                step = step.split('. ', 1)[1]
            steps.append(step)
        if line.strip().startswith('OUTPUT FORMAT:'):
            in_steps = False
    
    # Create trace entry
    trace_entry = AgentTrace(
        step=current_step + 1,
        agent="Planner",
        action="Created execution plan",
        outcome=f"Generated {len(steps)} steps"
    )
    
    return {
        "plan": plan_text,
        "plan_steps": steps,
        "trace": [trace_entry],
        "current_step": current_step + 1
    }