import os
import glob
import datetime
import json
import re
from typing import List, Dict, Optional
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


def extract_frontmatter_slug(content: str) -> Optional[str]:
    """Extract slug from YAML frontmatter if present."""
    # Match YAML frontmatter between --- delimiters
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not frontmatter_match:
        return None

    frontmatter = frontmatter_match.group(1)
    # Look for slug: "value" or slug: value
    slug_match = re.search(r'slug:\s*["\']?([^"\'\n]+)["\']?', frontmatter)
    if slug_match:
        return slug_match.group(1).strip()
    return None


def extract_text_from_md(filepath: str) -> tuple[str, Optional[str]]:
    """Extract text content and slug from markdown/MDX file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract slug from frontmatter
    slug = extract_frontmatter_slug(content)

    # Return raw text and slug
    return content, slug


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
        text = None
        slug = None

        if file['ext'] in ['md', 'mdx']:
            text, slug = extract_text_from_md(file['path'])
        elif file['ext'] == 'pdf':
            text = extract_text_from_pdf(file['path'])
        else:
            continue

        # Build metadata
        metadata = {
            'source': file['path'],
            'type': file['ext'],
            'modified': file['mtime'].isoformat()
        }

        # Add slug to metadata if found
        if slug:
            metadata['slug'] = slug

        documents.append(
            Document(
                page_content=text,
                metadata=metadata
            )
        )
    return documents

# Example usage:
if __name__ == '__main__':
    docs = load_documents_for_embedding()
    print(f'Found {len(docs)} new/updated documents for embedding.')
    update_last_rebuild_time() 