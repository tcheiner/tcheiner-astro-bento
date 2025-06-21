from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
import os

from chatbot.document_loader import vectorstore

load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")

# Define the path where the FAISS index will be saved (inside the backend directory)
backend_dir = "/tcheiner-astro-bento/backend"
faiss_index_path = os.path.join(backend_dir, "faiss_index")
blog_dir = "/tc-astro-bento/dist"
vectorstore = None

# Check if the FAISS index exists
if not os.path.exists(os.path.join(faiss_index_path, "index.faiss")):
    print("FAISS index not found. Creating a new one...")

    # Example documents
    documents = [
        {"page_content": "This is document 1", "metadata": {"source": "doc1"}},
        {"page_content": "This is document 2", "metadata": {"source": "doc2"}},
    ]

    # Create embeddings and FAISS index
    embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
    vectorstore = FAISS.from_documents(documents, embeddings)

    # Save the FAISS index
    vectorstore.save_local(faiss_index_path)
else:
    print("FAISS index found. Loading...")

# Load the FAISS index
vectorstore = FAISS.load_local(
                    faiss_index_path,
                    OpenAIEmbeddings(openai_api_key=openai_key))

# Process PDFs in the blog directory
pdf_files = [f for f in os.listdir(blog_dir) if f.endswith(".pdf")]
print("PDF files in blog directory:", pdf_files)

for pdf_file in pdf_files:
    pdf_path = os.path.join(blog_dir, pdf_file)
    print("Processing PDF:", pdf_path)
    # Add your PDF processing logic here

# Define a custom prompt template
prompt_template = """
                    You are TC Heiner. Use the following context to answer the user's question.
                    If you don't know the answer, say you don't know. Do NOT make anything up.
                    
                    Context:
                    {context}
                    
                    Question:
                    {question}
                    
                    Answer:
                    """
PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

# Create the RetrievalQA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=OpenAI(model="gpt-3.5-turbo", openai_api_key=openai_key),  # Use OpenAI GPT model
    retriever=vectorstore.as_retriever(),
    return_source_documents=True,
    chain_type_kwargs={"prompt": PROMPT}
)

# Query the chatbot
def ask_question(question):
    response = qa_chain({"query": question})
    answer = response["result"]
    sources = response["source_documents"]
    return answer, sources

# Example query
question = "Can you summarize my resume?"
answer, sources = ask_question(question)
print("Answer:", answer)
print("Sources:", [source.metadata["source"] for source in sources])


def get_mock_response(question: str) -> str:
    """
    Mock response generator for chatbot queries.
    """
    # You can replace this with real AI logic in the future
    if "hello" in question.lower():
        return "Hi there! How can I help you today?"
    elif "help" in question.lower():
        return "Sure, let me assist you with that."
    else:
        return "Sorry, I'm just a mock bot and don't have a real answer for that."
