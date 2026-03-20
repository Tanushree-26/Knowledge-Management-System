# Knowledge Management System -RAG Assistant

An intelligent, secure, and fully local Document Retrieval-Augmented Generation (RAG) system. This application effortlessly syncs documents from a specified Google Drive folder, parses the textual data at high speed, and stores it in a sophisticated vector database. 

It features an AI-powered conversational Assistant specifically tuned to act as an expert project consultant, delivering insights based strictly on your document context while meticulously hiding sensitive corporate secrets.


---

## 🚀 Key Features

*   **Google Drive Ingestion Pipeline**: Connects natively to Google Drive via OAuth2 to pull remote documents into your local environment.
*   **High-Speed PDF Parsing**: Utilizes Langchain's `PyPDFLoader` to rapidly rip textual streams natively out of PDFs without the overhead of heavy optical character recognition dependencies.
*   **Rate-Limit Protected Vector Operations**: The ingestion engine dynamically throttles document chunk uploads, successfully circumventing Google Gemini's free tier 100 requests-per-minute ceiling without crashing.
*   **Dual-Database Architecture**:
    *   **ChromaDB**: Persists semantic text chunks for high-dimensional similarity searches.
    *   **SQLite (`metadata_store`)**: Organizes structured document metadata, organizing records into `Project Title`, `Company Name`, and `Report Objective`.
*   **Confidentiality-First AI Agent**: Powered by `gemini-2.5-flash`, the underlying LLM agent is strictly prompt-engineered to *never* disclose raw confidential properties (like company names, revenue figures, or internal trade secrets), restricting outputs to technical project insights only.
*   **Streamlit Web Interface**: Features dual views—a dynamic Chatbot interface for conversational queries mapped with sources, and a structured Knowledge Browser displaying the current underlying SQLite catalog.

---

## 🔮 Future Scalability (Blob Storage Integration)
To transition this pipeline to an enterprise-grade production environment, the architecture can be decoupled using **Blob Storage (e.g., AWS S3, Azure Blob, Google Cloud Storage)**:
1. **Static Data Lake**: Instead of temporarily downloading files, documents can be securely synced from Google Drive into a persistent, static Blob Storage bucket.
2. **Direct VectorDB Connection**: The Vector Database will establish a direct, static connection to the Blob Storage. 
3. **Automated Embedding Generation**: Whenever the Blob Storage gets updated (e.g., new raw files are pushed or modified), the Vector Database will seamlessly trigger and make the new embeddings on the fly, completely decoupling your file storage from the high-speed search index.

---

## 📂 Project Structure

*   `app.py`: The main Streamlit graphical user interface. Features the chat timeline and the knowledge explorer.
*   `ingest_drive.py`: The primary ETL script. Run this to authenticate, download files, extract the native PDF text, split into manageable chunks, and pipe them directly into the databases.
*   `engine.py`: Defines the LangChain Question-Answer retrieval pipeline and the strict internal consultant system prompt.
*   `vectore_store.py`: Manages the local `Chroma` DB and integrates `models/gemini-embedding-001` with chunk batching controls.
*   `metadata_store.py`: Manages the local `metadata.db` SQLite connection, handling relational entity mappings seamlessly.

---

## ⚙️ Setup & Installation

1. **Install Dependencies**
    Ensure you have Python 3.9+ installed via Anaconda or natively.
    ```bash
    pip install -r requirements.txt
    ```

2. **Google Drive API Credentials**
    *   Enable the Google Drive API in your Google Cloud Console.
    *   Create OAuth 2.0 Client IDs and download the JSON file. Rename it to `credentials.json` and place it in the root folder.
    *   *Upon your first pipeline run, a browser window will automatically ask you to sign in. This generates the `token.json` file automatically.*

3. **Configure Environment Variables**
    Create a `.env` file in the root directory:
    ```env
    GOOGLE_API_KEY=your_gemini_api_key_here
    GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id_here
    ```

---

## 💻 Usage Instructions

### 1. Ingest Your Data
Before asking questions, populate your Knowledge Base by running the ingestion script. This downloads the PDFs, parses the fast-text stream, and embeds them securely.
```bash
python ingest_drive.py
```
*(Note: The console will visualize a progress bar. The script will safely pause for 60 seconds whenever it reaches 80 chunks to perfectly respect Google's Embedding API limits).*

### 2. Launch the Web App
Once ingestion is complete and your `chroma_db` directory is populated, spin up the local graphical dashboard:
```bash
streamlit run app.py
```

### 3. Interact Safely!
Ask the Assistant questions explicitly regarding the technical elements of your projects (e.g., solar power, car emissions). The Assistant tracks document sources and guarantees confidentiality protection regarding proprietary company properties natively.