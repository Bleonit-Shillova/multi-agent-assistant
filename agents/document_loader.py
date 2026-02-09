"""
Document Loader Module
This module handles loading and processing documents from the /data folder.
It splits documents into smaller chunks and stores them in a vector database
so our Research Agent can search through them.
"""

import os
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
)
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from agents.config import OPENAI_API_KEY, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP


class DocumentLoader:
    """
    Handles loading documents and creating a searchable vector database.
    
    What is a vector database?
    - It converts text into numbers (vectors) that represent meaning
    - Similar texts have similar vectors
    - This lets us find relevant documents by searching for similar meanings
    """
    
    def __init__(self, data_directory: str = "data"):
        """
        Initialize the document loader.
        
        Args:
            data_directory: Where your documents are stored
        """
        self.data_directory = data_directory
        
        # Create the embeddings model (converts text to vectors)
        self.embeddings = OpenAIEmbeddings(
            api_key=OPENAI_API_KEY,
            model=EMBEDDING_MODEL
        )
        
        # Text splitter breaks documents into smaller chunks
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )
        
        # This will store our vector database
        self.vector_store = None
    
    def load_documents(self) -> List:
        """
        Load all documents from the data directory.
        Supports: .txt, .pdf, .md files
        
        Returns:
            List of loaded documents
        """
        documents = []
        
        # Check if data directory exists
        if not os.path.exists(self.data_directory):
            os.makedirs(self.data_directory)
            print(f"Created {self.data_directory} folder. Please add documents there.")
            return documents
        
        # Load different file types
        for filename in os.listdir(self.data_directory):
            filepath = os.path.join(self.data_directory, filename)
            
            try:
                if filename.endswith('.txt') or filename.endswith('.md'):
                    loader = TextLoader(filepath)
                    documents.extend(loader.load())
                    print(f"Loaded: {filename}")
                    
                elif filename.endswith('.pdf'):
                    loader = PyPDFLoader(filepath)
                    documents.extend(loader.load())
                    print(f"Loaded: {filename}")
                    
            except Exception as e:
                print(f"Error loading {filename}: {e}")
        
        return documents
    
    def create_vector_store(self) -> Chroma:
        """
        Process documents and create the searchable vector database.
        
        Returns:
            Chroma vector store for searching
        """
        # Load all documents
        documents = self.load_documents()
        
        if not documents:
            print("No documents found. Please add files to the /data folder.")
            return None
        
        # Split documents into chunks
        print(f"Splitting {len(documents)} documents into chunks...")
        chunks = self.text_splitter.split_documents(documents)
        print(f"Created {len(chunks)} chunks")
        
        # Create the vector store
        print("Creating vector database (this may take a moment)...")
        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory="./chroma_db"  # Save to disk
        )
        
        print("Vector database created successfully!")
        return self.vector_store
    
    def get_retriever(self, k: int = 4):
        """
        Get a retriever that can search through documents.
        
        Args:
            k: Number of relevant chunks to return
            
        Returns:
            A retriever object for searching
        """
        if self.vector_store is None:
            # Try to load existing database
            if os.path.exists("./chroma_db"):
                self.vector_store = Chroma(
                    persist_directory="./chroma_db",
                    embedding_function=self.embeddings
                )
            else:
                self.create_vector_store()
        
        if self.vector_store is None:
            return None
            
        return self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )