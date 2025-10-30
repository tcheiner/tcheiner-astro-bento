import sys
sys.path.append('.')
import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# Set the API key
os.environ['OPENAI_API_KEY'] = ''
question = 'Tell us about your favorite thing you built. Share the technical challenges, your approach, and why you are proud of it.'

try:
    # Load vectorstore
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.load_local("chatbot/faiss_index", embeddings, allow_dangerous_deserialization=True)
    
    # Get the documents that would be used
    docs = vectorstore.similarity_search(question, k=5)
    
    print("=== DOCUMENTS BEING SENT TO GPT ===")
    for i, doc in enumerate(docs):
        print(f"\nDoc {i+1} - {doc.metadata.get('source', 'Unknown')}")
        print(doc.page_content[:500] + "...")
        print("---")
    
    # Create the same prompt template as the actual chatbot
    template = """Use the following pieces of context to answer the question. If you don't know the answer based on the context provided, just say that you don't know, don't try to make up an answer.

Context:
{context}

Question: {question}

Answer as TC Heiner in first person, and keep your response concise (under 150 words). Focus on professional experiences, projects, and achievements that are directly mentioned in the context."""

    prompt = PromptTemplate(
        template=template,
        input_variables=["context", "question"]
    )
    
    # Create QA chain
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=150,
        openai_api_key=os.environ['OPENAI_API_KEY']
    )
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )
    
    print("\n=== GPT RESPONSE ===")
    result = qa_chain.invoke({"query": question})
    print("Answer:", result["result"])
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
