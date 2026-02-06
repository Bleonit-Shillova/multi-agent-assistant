# Multi-Agent Research & Action Assistant

A multi-agent AI system that coordinates specialized agents to answer business questions based on uploaded documents.

## 🎯 Features

- **Multi-Agent Architecture**: Planner → Researcher → Writer → Verifier workflow
- **Document-Grounded Responses**: All answers cite source documents
- **Hallucination Prevention**: Verifier agent catches unsupported claims
- **Transparent Tracing**: See exactly which agent did what
- **Streamlit Web UI**: Easy-to-use interface

## 🏗️ Architecture
```
User Request
     ↓
┌─────────────────┐
│  Planner Agent  │  → Creates execution plan
└────────┬────────┘
         ↓
┌─────────────────┐
│ Research Agent  │  → Searches documents, returns cited notes
└────────┬────────┘
         ↓
┌─────────────────┐
│  Writer Agent   │  → Creates final deliverable
└────────┬────────┘
         ↓
┌─────────────────┐
│ Verifier Agent  │  → Checks accuracy, citations, safety
└────────┬────────┘
         ↓
    Final Output
```

## 📁 Project Structure
```
multi-agent-assistant/
├── app/
│   ├── __init__.py
│   └── main.py              # Streamlit web interface
├── agents/
│   ├── __init__.py
│   ├── config.py            # Configuration and API keys
│   ├── state.py             # Shared state definition
│   ├── document_loader.py   # Document processing
│   ├── planner.py           # Planner Agent
│   ├── researcher.py        # Research Agent
│   ├── writer.py            # Writer Agent
│   ├── verifier.py          # Verifier Agent
│   └── workflow.py          # LangGraph orchestration
├── data/
│   ├── project_report.md    # Sample document
│   └── weekly_update.md     # Sample document
├── eval/
│   ├── __init__.py
│   └── test_cases.py        # Evaluation tests
├── .env                     # API keys (not in git)
├── .gitignore
├── requirements.txt
└── README.md
```

## 🚀 Setup Instructions

### Prerequisites
- Python 3.11+
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR-USERNAME/multi-agent-assistant.git
cd multi-agent-assistant
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file with your API key:
```
OPENAI_API_KEY=sk-your-key-here
```

5. Add documents to the `/data` folder (samples included)

### Running the Application
```bash
python -m streamlit run app/main.py
```

The app will open in your browser at http://localhost:8501

### Running Tests
```bash
python eval/test_cases.py
```

## 💡 Example Tasks

- "Summarize the top 5 risks and propose mitigations"
- "Create a client update email from the weekly report"
- "Extract all deadlines and owners into an action list"
- "Compare two approaches and recommend one with justification"

## 🔒 Safety Features

- **Grounded Responses**: Only uses information from provided documents
- **Citation Required**: All facts must have source citations
- **Hallucination Detection**: Verifier flags unsupported claims
- **"I Don't Know"**: System admits when information isn't available
- **Prompt Injection Defense**: Detects suspicious instructions in documents

## 📊 Agent Trace Example

| Step | Agent | Action | Outcome |
|------|-------|--------|---------|
| 1 | Planner | Created execution plan | Generated 4 steps |
| 2 | Researcher | Searched 6 document chunks | Found 5 relevant findings |
| 3 | Writer | Generated draft deliverable | Created 1500 character document |
| 4 | Verifier | Verified draft accuracy | PASSED - Found 0 issues |

## 🛠️ Technologies Used

- **LangGraph**: Multi-agent orchestration
- **LangChain**: AI framework
- **OpenAI GPT-4**: Language model
- **ChromaDB**: Vector database for document search
- **Streamlit**: Web interface

## 📝 License

MIT License