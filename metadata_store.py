import sqlite3
import os

DB_PATH = "metadata.db"

def init_db():
    """Initializes the SQLite database with the required schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Created table with project_title instead of name
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drive_metadata (
            id TEXT PRIMARY KEY,
            project_title TEXT,
            company_name TEXT,
            report_objective TEXT,
            mimeType TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_metadata(files):
    """
    Saves a list of file metadata dictionaries to the database.
    Expected files to possess 'id', 'project_title', 'company_name', 'report_objective', and 'mimeType' keys.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for file in files:
        # Fallback to 'name' if 'project_title' isn't explicitly set during API extraction
        p_title = file.get('project_title') or file.get('name')
        
        cursor.execute('''
            INSERT OR REPLACE INTO drive_metadata (id, project_title, company_name, report_objective, mimeType)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            file.get('id'), 
            p_title,
            file.get('company_name'),
            file.get('report_objective'),
            file.get('mimeType')
        ))
        
    conn.commit()
    conn.close()
    print(f"Secured metadata for {len(files)} originally hosted files to {DB_PATH}.")

def get_all_metadata():
    """Retrieves all indexed metadata from the SQLite database."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, project_title, company_name, report_objective, mimeType FROM drive_metadata")
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        print(f"Schema mismatch detected. Ensure {DB_PATH} uses the latest schema (you might need to delete it and re-ingest).")
        rows = []
    
    conn.close()
    
    # Return formatted list of dictionaries suitable for Streamlit dataframe
    return [
        {
            "ID": row[0], 
            "Project Title": row[1], 
            "Company Name": row[2],
            "Report Objective": row[3],
            "File Type": row[4]
        } for row in rows
    ]
