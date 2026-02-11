"""
Configuration settings for our multi-agent system.
This file loads our API keys and sets up basic parameters.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Try Streamlit secrets first (for Streamlit Cloud), then fall back to .env
try:
    import streamlit as st
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", None)
except Exception:
    OPENAI_API_KEY = None

if not OPENAI_API_KEY:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Check if key exists
if not OPENAI_API_KEY:
    raise ValueError("Please set OPENAI_API_KEY in your .env file or Streamlit secrets")

# Model settings 
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4-turbo-preview")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Optional: cheaper mode for eval/dev
FAST_EVAL = os.getenv("FAST_EVAL", "false").lower() == "true"
if FAST_EVAL:
    DEFAULT_MODEL = os.getenv("FAST_EVAL_MODEL", "gpt-3.5-turbo")

# Chunk settings for document processing
CHUNK_SIZE = 1000  # How many characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks for context