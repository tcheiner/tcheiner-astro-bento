from langchain.document_loaders import TextLoader, PyPDFLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
import os

# Step 1: Load all documents from the folder
def load_documents(folder_path):
    loaders = []
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        if file.endswith(".md"):
            loaders.append(UnstructuredMarkdownLoader(file_path))
        elif file.endswith(".pdf"):
            loaders.append(PyPDFLoader(file_path))
        elif file.endswith(".txt"):
            loaders.append(TextLoader(file_path))
    docs = []
    for loader in loaders:
        docs.extend(loader.load())
    return docs

# Step 2: Split documents into chunks
def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return text_splitter.split_documents(documents)

# Step 3: Embed documents and store in FAISS
def create_vectorstore(documents, vectorstore_path="faiss_index"):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(vectorstore_path)
    return vectorstore

# Main: Load, split, and embed documents
folder_path = "documents"  # Path to your folder
documents = load_documents(folder_path)
split_docs = split_documents(documents)
vectorstore = create_vectorstore(split_docs)
print("Documents loaded and stored in FAISS!")
