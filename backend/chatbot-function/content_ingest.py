import os
import glob
import datetime
import json
from typing import List, Dict
from langchain_core.documents import Document
try:
    import markdown
except ImportError:
    markdown = None
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# Path to the content directory (relative to project root)
CONTENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/content'))
REBUILD_TRACK_FILE = os.path.join(os.path.dirname(__file__), 'last_rebuild.json')


def get_last_rebuild_time() -> datetime.datetime:
    if not os.path.exists(REBUILD_TRACK_FILE):
        return datetime.datetime.fromtimestamp(0)
    with open(REBUILD_TRACK_FILE, 'r') as f:
        data = json.load(f)
        return datetime.datetime.fromisoformat(data.get('last_rebuild'))


def update_last_rebuild_time():
    now = datetime.datetime.now().isoformat()
    with open(REBUILD_TRACK_FILE, 'w') as f:
        json.dump({'last_rebuild': now}, f)


def extract_text_from_md(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    # Optionally strip frontmatter and MDX components here
    # For now, just return the raw text
    return content


def extract_text_from_pdf(filepath: str) -> str:
    if PyPDF2 is None:
        raise ImportError('PyPDF2 is required for PDF extraction')
    text = ''
    with open(filepath, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ''
    return text


def find_new_content_files(since: datetime.datetime) -> List[Dict]:
    exts = ['md', 'mdx', 'pdf']
    files = []
    for ext in exts:
        pattern = os.path.join(CONTENT_DIR, f'**/*.{ext}')
        for filepath in glob.glob(pattern, recursive=True):
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
            if mtime > since:
                files.append({'path': filepath, 'ext': ext, 'mtime': mtime})
    return files


def load_documents_for_embedding() -> List[Document]:
    last_rebuild = get_last_rebuild_time()
    files = find_new_content_files(last_rebuild)
    documents = []
    for file in files:
        if file['ext'] in ['md', 'mdx']:
            text = extract_text_from_md(file['path'])
        elif file['ext'] == 'pdf':
            text = extract_text_from_pdf(file['path'])
        else:
            continue
        documents.append(
            Document(
                page_content=text,
                metadata={
                    'source': file['path'],
                    'type': file['ext'],
                    'modified': file['mtime'].isoformat()
                }
            )
        )
    return documents

# Example usage:
if __name__ == '__main__':
    docs = load_documents_for_embedding()
    print(f'Found {len(docs)} new/updated documents for embedding.')
    update_last_rebuild_time() 