from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from vectore_store import get_vector_store
import os
from dotenv import load_dotenv

load_dotenv()

def get_rag_chain():
    """Builds and returns the RAG pipeline chain."""
    # Setup the requested LLM. Uses Gemini for reasoning.
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
    
    # Retrieve the vector store and configure it as a retriever
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    
    # Instruction Prompt Template
    system_prompt = (
        "You are an expert project consultant AI. Use the provided context retrieved "
        "from the document database to answer the user's question. "
        "You must ONLY provide insights about the type of project asked (e.g., solar power, car emission, etc.). "
        "STRICT CONFIDENTIALITY RULE: Under no circumstances should you reveal any hidden confidential features "
        "such as the company name, revenue, or any other secrets related to the company. "
        "If the answer is not in the context, clearly state that you do not have enough information to answer. "
        "Keep the answer concise and well-formatted.\n\n"
        "Context:\n{context}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])
    
    # Create the complete chain
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    return rag_chain

def query_rag(user_query: str):
    """Takes a user question and executes the RAG pipeline."""
    try:
        rag_chain = get_rag_chain()
        # The chain invokes by passing input and receives back context and answer
        response = rag_chain.invoke({"input": user_query})
        return {
            "answer": response.get("answer", "No answer could be generated."),
            "context": response.get("context", [])
        }
    except Exception as e:
        return {
            "answer": f"Error running complete RAG pipeline: {str(e)}",
            "context": []
        }
