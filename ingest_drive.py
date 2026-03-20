import os
import io
import shutil
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from vectore_store import add_documents_to_store
from metadata_store import save_metadata
from config import Google_API_KEY, Google_DRIVE

# Access scope for Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    """Authenticates the user and returns the Drive API service."""
    creds = None
    # token.json stores the user's access and refresh tokens.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    # If no valid credentials, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save credentials for next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def download_files_from_folder(service, folder_id, download_dir):
    """Lists and downloads files from the specified Google Drive folder."""
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        
    query = f"'{folder_id}' in parents and trashed = false"
    
    # Execute query to list files
    results = service.files().list(q=query, fields="nextPageToken, files(id, name, mimeType)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found in the specified folder.')
        return

    print(f'Found {len(items)} files. Downloading...')
    
    # Cache metadata for Google Drive items in local SQLite
    save_metadata(items)
    
    for item in items:
        file_id = item['id']
        file_name = item['name']
        mime_type = item['mimeType']
        
        # Skip Google Workspace specific documents (like Google Docs/Sheets)
        # In a real app, you might want to export these to PDF/Text first.
        if 'application/vnd.google-apps' in mime_type:
            print(f"Skipping native Google Workspace document: {file_name} (Consider adding an export step)")
            continue

        request = service.files().get_media(fileId=file_id)
        file_path = os.path.join(download_dir, file_name)
        
        with io.FileIO(file_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    print(f"Downloaded {file_name} {int(status.progress() * 100)}%.")

def main():
    load_dotenv()
    folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    if not folder_id:
        print("Please configure GOOGLE_DRIVE_FOLDER_ID in the .env file.")
        return

    print("Authenticating with Google Drive...")
    try:
        service = get_drive_service()
    except Exception as e:
        print(f"Authentication failed: {e}\\nPlease ensure credentials.json is configured correctly.")
        return
    
    download_dir = "./temp_drive_files"
    print(f"Downloading files from folder {folder_id}...")
    download_files_from_folder(service, folder_id, download_dir)
    
    # Check if download triggered
    if not os.path.exists(download_dir) or not os.listdir(download_dir):
        print("No viable files were downloaded. Exiting.")
        if os.path.exists(download_dir):
            shutil.rmtree(download_dir)
        return

    # Load downloaded documents using LangChain's fast native PDF parser
    print("Loading documents from temp folder using high-speed PyPDFLoader...")
    try:
        from langchain_community.document_loaders import PyPDFLoader
        
        # PyPDFLoader parses the raw text stream inside the PDF. This takes SECONDS instead of hours, 
        # but it will not run optical character recognition on embedded images.
        loader = DirectoryLoader(
            download_dir,
            glob="**/*.pdf",
            loader_cls=PyPDFLoader,
            use_multithreading=True,
            show_progress=True
        )
        documents = loader.load()
        print(f"Successfully loaded {len(documents)} documents via fast text extraction.")
    except Exception as e:
        print(f"Error loading documents: {e}")
        documents = []
    
    if not documents:
        print("No documents were loaded to be processed. Exiting.")
        shutil.rmtree(download_dir)
        return

    # Split documents into smaller manageable chunks suitable for API limits
    # Since each document contains ~250 pages, we keep chunks reasonable to not 
    # overload free-tier API tokens. Max tokens for embedding-001 is typically 2048.
    print("Chunking documents (tailored for 250-page complex docs)...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=250)
    chunks = text_splitter.split_documents(documents)
    print(f"Split documents into {len(chunks)} chunks.")
    
    # Push the generated chunks to the vector store (Chroma)
    print("Pushing chunks to the vector database with API limit handling...")
    add_documents_to_store(chunks)
    
    # Cleanup downloaded files after ingestion
    print("Cleaning up temporary directory...")
    shutil.rmtree(download_dir)
    print("Ingestion pipeline finished successfully!")

if __name__ == '__main__':
    main()
