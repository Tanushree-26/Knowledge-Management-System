import os
import time
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

VECTOR_STORE_DIR = "./chroma_db"

def get_vector_store():
    """Initializes and returns the Chroma vector database."""
    # Initializing Google GenAI Embeddings using free tier capabilities
    # Uses GOOGLE_API_KEY from environment variables
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    # Initialize Chroma vector store with persistent directory
    vector_store = Chroma(
        collection_name="drive_documents_local",
        embedding_function=embeddings,
        persist_directory=VECTOR_STORE_DIR
    )
    return vector_store

def add_documents_to_store(docs):
    """
    Takes chunks of documents and adds them to the vector store.
    Utilizes chunk batching and delays to respect the Free Tier Google API rate limits.
    """
    vector_store = get_vector_store()
    
    # Chunking strategy for embedding API limits:
    # Google free tier API has a strict limit of exactly 100 requests per minute
    # for embeddings. Processing 3x 250-page docs will hit this. We throttle it securely.
    batch_size = 80 
    pause_time = 60 # wait a full 60 seconds to reset the 100 req/min quota
    
    total_batches = (len(docs) + batch_size - 1) // batch_size
    
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i + batch_size]
        current_batch = i // batch_size + 1
        print(f"Adding batch {current_batch} of {total_batches} to the vector store...")
        
        vector_store.add_documents(batch)
        
        if i + batch_size < len(docs):
            print(f"Waiting {pause_time} seconds to respect free tier API rate limits...")
            time.sleep(pause_time)
            
    print(f"Successfully added all {len(docs)} document chunks to the vector store.")
