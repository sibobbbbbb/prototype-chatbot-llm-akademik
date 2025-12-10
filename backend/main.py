import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import requests
from fastapi.middleware.cors import CORSMiddleware
from utils import parse_query, rerank_results, merge_adjacent_chunks

DB_DIR = "../chroma_db"
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral-itb"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

print("⏳ Loading Database...")
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_db = Chroma(persist_directory=DB_DIR, embedding_function=embedding_model)
print("✅ Ready!")

class ChatRequest(BaseModel):
    question: str

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    print(f"\n🔎 Question: {req.question}")
    
    # Parse query
    query_info = parse_query(req.question)
    print(f"📊 Query Analysis: {query_info}")
    
    # Hybrid Search
    results = []
    
    # Strategy A: Filter by article numbers
    if query_info['article_numbers']:
        print(f"🎯 Searching for specific articles: {query_info['article_numbers']}")
        
        for article_num in query_info['article_numbers']:
            # Metadata filter
            filtered_results = vector_db.similarity_search(
                req.question,
                k=5,
                filter={"article_number": article_num}
            )
            results.extend(filtered_results)
            print(f"   -> Found {len(filtered_results)} chunks for Article {article_num}")
        
        # Fallback to semantic search if no results
        if not results:
            print("⚠️  Metadata filter found no results, falling back to semantic search...")
            results = vector_db.similarity_search(req.question, k=10)
    
    # Strategy B: Calendar query
    elif query_info['doc_type'] == 'kalender':
        print(f"📅 Searching in Calendar...")
        
        # Filter by month if available
        if query_info['months']:
            print(f"   🔍 Filter by month: {query_info['months']}")
            for month in query_info['months']:
                filtered_results = vector_db.similarity_search(
                    req.question,
                    k=5,
                    filter={"month": month}
                )
                results.extend(filtered_results)
                print(f"   -> Found {len(filtered_results)} chunks for {month}")
        
        # Fallback to semantic search in calendar documents
        if not results:
            print("   🔍 Semantic search in calendar documents...")
            results = vector_db.similarity_search(
                req.question,
                k=10,
                filter={"doc_type": "kalender"}
            )
    
    # Strategy C: General query, pure semantic search
    else:
        print("🔍 Semantic search for general query...")
        results = vector_db.similarity_search(req.question, k=10)
    
    # Re-rank results
    if results:
        print(f"🔄 Re-ranking {len(results)} results...")
        results = rerank_results(results, query_info)
    
    print("--- TOP RESULTS AFTER RE-RANKING ---")
    relevant_context = []
    
    for idx, doc in enumerate(results[:5]):
        content = doc.page_content
        article_num = doc.metadata.get('article_number', 'N/A')
        page = doc.metadata.get('page', 0)
        source = doc.metadata.get('source', 'Unknown')
        
        print(f"{idx+1}. {source} Page {page} | Article: {article_num}")
        print(f"   {content[:100]}...")
        
        relevant_context.append(content)
    
    # Context Enrichment
    if query_info['query_type'] == 'specific_article' and len(relevant_context) > 0:
        context_text = "\n\n---\n\n".join(relevant_context[:3])
    else:
        context_text = "\n\n---\n\n".join(relevant_context)
    
    # Get sources
    sources = []
    seen = set()
    for doc in results[:5]:
        source_str = f"{doc.metadata.get('source')} (Page. {doc.metadata.get('page', 0) + 1})"
        if source_str not in seen:
            sources.append(source_str)
            seen.add(source_str)

    # Prompt Engineering
    if query_info['query_type'] == 'specific_article':
        prompt = f"""[INST] You are an ITB academic assistant expert in academic regulations.

TASK:
The user is asking for a specific article. You MUST:
1. Find the requested article in the CONTEXT
2. Quote the content of the article COMPLETELY
3. If the article has sub-sections, mention all of them
4. DO NOT say "not found" if the article is in the CONTEXT

CONTEXT:
{context_text}

QUESTION:
{req.question}

Answer in the format:
"Article [number]: [full content of the article]" [/INST]
"""
    elif query_info['query_type'] == 'specific_date' or query_info['doc_type'] == 'kalender':
        prompt = f"""[INST] You are an ITB academic assistant expert in the academic calendar.

TASK:
The user is asking for information about academic schedules/events. You MUST:
1. Find relevant dates and events in the CONTEXT
2. Mention the full date with the event description
3. If there are multiple events, list them all in a structured manner
4. Provide clear and easy-to-understand information

CONTEXT:
{context_text}

QUESTION:
{req.question}

Answer in a clear format, including the full date and event description. [/INST]
"""
    elif query_info['query_type'] == 'comparison':
        prompt = f"""[INST] You are an ITB academic assistant expert in academic regulations.

TASK:
The user is comparing several articles. You MUST:
1. Explain each article mentioned
2. Compare their differences and similarities
3. Provide a clear and structured explanation

CONTEXT:
{context_text}

QUESTION:
{req.question} [/INST]
"""
    else:
        prompt = f"""[INST] You are an ITB academic assistant expert in academic regulations.

TASK:
Answer the user's question based on the provided CONTEXT.
- Answer factually and concisely
- Quote relevant articles/sections if any
- Use good Indonesian language

CONTEXT:
{context_text}

QUESTION:
{req.question} [/INST]
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 4096}
    }

    try:
        print("🤖 Sending to AI...")
        res = requests.post(OLLAMA_API_URL, json=payload)
        answer = res.json().get("response", "")
        return {"answer": answer, "sources": sources}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error AI")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)