"""
Configuration settings for our multi-agent system.
This file loads our API keys and sets up basic parameters.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Check if key exists
if not OPENAI_API_KEY:
    raise ValueError("Please set OPENAI_API_KEY in your .env file")

# Model settings
DEFAULT_MODEL = "gpt-4-turbo-preview"  # You can also use "gpt-3.5-turbo" for cheaper testing
EMBEDDING_MODEL = "text-embedding-3-small"  # For document search

# Chunk settings for document processing
CHUNK_SIZE = 1000  # How many characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks for context