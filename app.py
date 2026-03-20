import streamlit as st
import os
from engine import query_rag
from dotenv import load_dotenv
from metadata_store import get_all_metadata
load_dotenv()

st.set_page_config(page_title="Semantic Drive Q&A", layout="centered", page_icon="🔍")

st.title("Semantic Assistant RAG Prototype 🧠")
st.markdown("""
Welcome! This application searches through the documents that have been synced from Google Drive 
and provides a contextually-aware answer based on the local Vector Database. 
*Ensure you have run `python ingest_drive.py` first to populate the vector store.*
""")

st.divider()

# Create Tabs for the Presentation Layer
tab_chat, tab_browse = st.tabs(["💬 Search & Q&A", "📂 Knowledge Browser"])

with tab_chat:
    # User prompt input
    if prompt := st.chat_input("Ask a question regarding your Drive documents..."):
        # Display the user's message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get the LLM response equipped with Retrival Context
        with st.chat_message("assistant"):
            with st.spinner("Searching database and thinking..."):
                result = query_rag(prompt)
                
                raw_answer = result.get('answer', "An unexpected error occurred.")
                sources = result.get('context', [])
                
                # Format the answer with retrieved document sources
                if sources:
                    source_filenames = list(set([os.path.basename(doc.metadata.get('source', 'Unknown')) for doc in sources]))
                    source_bullets = "\n".join([f"- `{src}`" for src in source_filenames if src != 'Unknown'])
                    
                    if source_bullets:
                        full_response = f"{raw_answer}\n\n**Sources:**\n{source_bullets}"
                    else:
                        full_response = raw_answer
                else:
                    full_response = raw_answer

            st.markdown(full_response)

with tab_browse:
    st.subheader("Available Knowledge Base")
    st.markdown("Here is the list of documents currently cataloged in the metadata store from Google Drive.")
    
    try:
        metadata = get_all_metadata()
        if metadata:
            st.dataframe(metadata, use_container_width=True, hide_index=True)
        else:
            st.info("No documents found in the underlying Knowledge Base. Please run the ingestion script.")
    except Exception as e:
        st.error(f"Could not load Knowledge Browser: {e}")
