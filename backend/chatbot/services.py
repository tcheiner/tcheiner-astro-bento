# Normal imports - no more lazy loading needed with container images
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

from dotenv import load_dotenv
import os

from . import content_ingest

load_dotenv()
openai_key = os.environ.get("OPENAI_API_KEY")

# Define the path where the FAISS index will be saved (inside the chatbot directory)
chatbot_dir = os.path.dirname(__file__)
faiss_index_path = os.path.join(chatbot_dir, "faiss_index")
blog_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/content'))

prompt_template = """
You are TC Heiner, a senior software engineer and technical architect, having a professional conversation about your documented experience and projects.

BETA NOTICE: Start your response with a brief note that this chatbot is in beta testing, then proceed with your answer.

STRICT ACCURACY RULES:
- Only use information explicitly provided in the context
- Never invent experiences, projects, or technical details
- If context is insufficient, clearly state "I don't have that specific information documented"
- When explaining technical decisions, only reference what's documented in the context

RESPONSE STYLE:
- Answer in first person as TC
- Be conversational but precise
- Provide specific examples from the context when available
- Explain technical reasoning based on documented decisions
- Include links when referencing blog posts: "You can read more about this in my post: [Title](https://tcheiner.com/posts/slug)"

DOCUMENTED BACKGROUND:
Your experience includes 17+ years in software engineering, progression from developer to staff engineer at Wells Fargo, and recent roles as Founding Engineer at ManaBurn and Cloud Architect at Myndsens. Documented expertise areas include Python, Java, AWS, AI/ML technologies, containerization, and technical leadership.

Context: {context}
Question: {question}

Answer: """
def rebuild_vectorstore():
    """
    Rebuilds the FAISS vectorstore from new/updated documents.
    """
    documents = content_ingest.load_documents_for_embedding()
    embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
    if documents:
        print(f"Embedding {len(documents)} new/updated documents...")
        if not os.path.exists(os.path.join(faiss_index_path, "index.faiss")):
            # Create new FAISS index
            vectorstore = FAISS.from_documents(documents, embeddings)
        else:
            # Load existing index and add new docs
            vectorstore = FAISS.load_local(faiss_index_path, embeddings, allow_dangerous_deserialization=True)
            vectorstore.add_documents(documents)
        # Save updated index
        vectorstore.save_local(faiss_index_path)
        # Update the last rebuild time
        content_ingest.update_last_rebuild_time()
        return vectorstore
    else:
        print("No new or updated documents to embed.")
        # Load the existing index
        vectorstore = FAISS.load_local(faiss_index_path, embeddings, allow_dangerous_deserialization=True)
        return vectorstore

def get_local_vectorstore():
    """
    Loads the local FAISS vectorstore from disk.
    """
    embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
    return FAISS.load_local(faiss_index_path, embeddings, allow_dangerous_deserialization=True)

def get_lambda_vectorstore():
    LAYER_PATH = "/opt/python/faiss_index"  # /opt is where Lambda layers are mounted
    faiss_index_path = LAYER_PATH
    openai_key = os.environ.get("OPENAI_API_KEY")
    embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
    return FAISS.load_local(faiss_index_path, embeddings, allow_dangerous_deserialization=True)

def get_qa_chain(vectorstore):
    PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    return RetrievalQA.from_chain_type(
        llm=ChatOpenAI(
            model="gpt-4o-mini",      # Better model for higher quality responses
            temperature=0.2,          # Low temperature for accuracy with slight personality
            max_tokens=400,           # Longer responses for comprehensive answers
            openai_api_key=openai_key
        ),
        retriever=vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 5,               # More context documents for better answers
                "score_threshold": 0.5  # Flexible similarity matching
            }
        ),
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )

def query_vectorstore(question):
    """
    Queries the vectorstore with the given question and returns the answer and sources.
    """
    # Check if running in Lambda environment
    if os.path.exists("/opt/python/faiss_index"):
        vectorstore = get_lambda_vectorstore()
    else:
        vectorstore = get_local_vectorstore()
    
    qa_chain = get_qa_chain(vectorstore)
    response = qa_chain.invoke({"query": question})
    answer = response["result"]
    sources = response["source_documents"]
    return answer, sources

def get_mock_response(question: str) -> str:
    """
    Mock response generator for chatbot queries.
    """
    if "hello" in question.lower():
        return "Hi there! How can I help you today?"
    elif "help" in question.lower():
        return "Sure, let me assist you with that."
    else:
        return "Sorry, I'm just a mock bot and don't have a real answer for that."


