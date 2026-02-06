"""
Streamlit Web Interface
This creates the user-facing application.
"""

import streamlit as st
import sys
import os

# Add parent directory to path so we can import agents
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.workflow import run_assistant, format_trace_table
from agents.document_loader import DocumentLoader


# Page configuration
st.set_page_config(
    page_title="Multi-Agent Research Assistant",
    page_icon="🤖",
    layout="wide"
)

# Title and description
st.title("Multi-Agent Research Assistant")
st.markdown("""
This assistant uses multiple AI agents to answer your questions based on uploaded documents:

1. **Planner Agent**: Breaks down your request into steps
2. **Research Agent**: Searches documents for relevant information
3. **Writer Agent**: Creates the final deliverable
4. **Verifier Agent**: Checks for accuracy and citations

*Add your documents to the `/data` folder and ask questions about them!*
""")

# Sidebar for document management
with st.sidebar:
    st.header("Document Management")
    
    # Check for documents
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    if os.path.exists(data_path):
        files = [f for f in os.listdir(data_path) if f.endswith(('.txt', '.md', '.pdf'))]
        if files:
            st.success(f"Found {len(files)} document(s):")
            for f in files:
                st.write(f"• {f}")
        else:
            st.warning("No documents found. Add .txt, .md, or .pdf files to the /data folder.")
    else:
        st.warning("Data folder not found.")
    
    # Rebuild index button
    if st.button("Rebuild Document Index"):
        with st.spinner("Rebuilding index..."):
            loader = DocumentLoader(data_directory=data_path)
            loader.create_vector_store()
            st.success("Index rebuilt!")
    
    st.markdown("---")
    st.header(" Example Tasks")
    st.markdown("""
    Try these example requests:
    
    - "Summarize the top 5 risks and propose mitigations"
    - "Create a client update email from the weekly report"
    - "Extract all deadlines and owners into an action list"
    - "What is the current budget status?"
    """)

# Main input area
st.header(" Ask a Question")

# User input
user_input = st.text_area(
    "Enter your request:",
    placeholder="Example: Summarize the key risks mentioned in the documents and draft an email to the client about them.",
    height=100
)

# Run button
if st.button(" Run Assistant", type="primary"):
    if not user_input.strip():
        st.error("Please enter a request.")
    else:
        # Create columns for output
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header(" Final Output")
            
            with st.spinner("Running multi-agent workflow..."):
                try:
                    # Run the assistant
                    result = run_assistant(user_input)
                    
                    # Display final output
                    if result.get("final_output"):
                        st.markdown(result["final_output"])
                    elif result.get("draft"):
                        st.markdown(result["draft"])
                    else:
                        st.warning("No output generated.")
                    
                    # Display verification status
                    if result.get("verification_passed") is not None:
                        if result["verification_passed"]:
                            st.success(" Verification: PASSED")
                        else:
                            st.warning(" Verification: Issues Found")
                            if result.get("issues_found"):
                                with st.expander("View Issues"):
                                    for issue in result["issues_found"]:
                                        st.write(f"• {issue}")
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.exception(e)
        
        with col2:
            st.header(" Agent Trace")
            
            # Display trace table
            if result.get("trace"):
                trace_md = format_trace_table(result["trace"])
                st.markdown(trace_md)
            
            # Display plan
            with st.expander(" View Plan"):
                if result.get("plan"):
                    st.markdown(result["plan"])
                else:
                    st.write("No plan generated.")
            
            # Display research notes
            with st.expander(" View Research Notes"):
                if result.get("research_notes"):
                    for i, note in enumerate(result["research_notes"], 1):
                        st.markdown(f"**Note {i}:**")
                        st.write(f"- Finding: {note['content']}")
                        st.write(f"- Source: {note['source']}")
                        st.markdown("---")
                else:
                    st.write("No research notes.")
            
            # Display verification details
            with st.expander(" View Verification Details"):
                if result.get("verification_result"):
                    st.markdown(result["verification_result"])
                else:
                    st.write("No verification performed.")

# Footer
st.markdown("---")
st.markdown("*Built with LangGraph + LangChain + OpenAI*")