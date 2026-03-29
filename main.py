import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2
from anthropic import Anthropic
from openai import OpenAI
from pydantic import BaseModel
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

app = FastAPI(title="AI Document Q&A System - Multi-Provider")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI clients (lazy initialization)
anthropic_client = None
openrouter_client = None

def get_anthropic_client():
    global anthropic_client
    if anthropic_client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if api_key:
            anthropic_client = Anthropic(api_key=api_key)
    return anthropic_client

def get_openrouter_client():
    global openrouter_client
    if openrouter_client is None:
        api_key = os.getenv("OPENROUTER_KEY", "")
        if api_key:
            openrouter_client = OpenAI(api_key=api_key, base_url="https://openrouter.io/api/v1")
    return openrouter_client

# In-memory storage for documents
documents_store = {}
vectorizer = TfidfVectorizer(max_features=100, stop_words='english')

class QueryRequest(BaseModel):
    question: str
    provider: str = "claude"

def extract_text_from_pdf(file):
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
        return text
    except Exception as e:
        raise ValueError(f"Error reading PDF: {str(e)}")

def chunk_text(text, chunk_size=500):
    """Split text into chunks for better processing"""
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def find_relevant_chunks(question, chunks, top_k=3):
    """Find most relevant chunks using TF-IDF similarity"""
    try:
        # Combine all chunks for vectorization
        all_texts = chunks + [question]
        vectors = vectorizer.fit_transform(all_texts)

        # Get similarity scores between question and chunks
        question_vector = vectors[-1]
        chunk_vectors = vectors[:-1]

        similarities = (chunk_vectors * question_vector.T).toarray().flatten()
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        relevant_chunks = [chunks[i] for i in top_indices if similarities[i] > 0]
        return relevant_chunks if relevant_chunks else chunks[:top_k]
    except Exception as e:
        # Fallback: return first chunks if vectorization fails
        return chunks[:top_k]

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF document"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        content = await file.read()

        # Create a file-like object from bytes
        from io import BytesIO
        pdf_file = BytesIO(content)

        # Extract text
        text = extract_text_from_pdf(pdf_file)

        if not text.strip():
            raise HTTPException(status_code=400, detail="PDF appears to be empty or unreadable")

        # Store document
        doc_id = file.filename.replace('.pdf', '')
        chunks = chunk_text(text)
        documents_store[doc_id] = {
            "filename": file.filename,
            "content": text,
            "chunks": chunks,
            "size": len(text)
        }

        return JSONResponse({
            "success": True,
            "message": f"Document '{file.filename}' uploaded successfully",
            "doc_id": doc_id,
            "text_length": len(text),
            "chunks_count": len(chunks)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def query_claude(question, context):
    """Query Claude API"""
    client = get_anthropic_client()
    if not client:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    system_prompt = """You are a helpful AI assistant specialized in answering questions about uploaded documents.
Use the provided document content to answer questions accurately. If the answer is not found in the documents,
clearly state that the information is not available in the provided documents."""

    user_message = f"""Question: {question}

Relevant document content:
{context}

Please answer the question based on the provided document content."""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )
    return response.content[0].text

def query_openrouter(question, context):
    """Query via OpenRouter (OpenAI-compatible)"""
    client = get_openrouter_client()
    if not client:
        raise ValueError("OPENROUTER_KEY not configured")

    system_prompt = """You are a helpful AI assistant specialized in answering questions about uploaded documents.
Use the provided document content to answer questions accurately. If the answer is not found in the documents,
clearly state that the information is not available in the provided documents."""

    user_message = f"""Question: {question}

Relevant document content:
{context}

Please answer the question based on the provided document content."""

    response = client.chat.completions.create(
        model="openai/gpt-4o",
        max_tokens=1024,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message.content

@app.post("/query")
async def query_document(request: QueryRequest):
    """Query uploaded documents using selected AI provider"""
    if not documents_store:
        raise HTTPException(status_code=400, detail="No documents uploaded. Please upload a document first.")

    if request.provider not in ["claude", "openrouter"]:
        raise HTTPException(status_code=400, detail="Provider must be 'claude' or 'openrouter'")

    if request.provider == "claude" and not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=400, detail="ANTHROPIC_API_KEY not configured")

    if request.provider == "openrouter" and not os.getenv("OPENROUTER_KEY"):
        raise HTTPException(status_code=400, detail="OPENROUTER_KEY not configured")

    try:
        all_chunks = []
        doc_names = []
        for doc_id, doc_data in documents_store.items():
            all_chunks.extend(doc_data["chunks"])
            doc_names.append(doc_data["filename"])

        relevant_chunks = find_relevant_chunks(request.question, all_chunks, top_k=5)
        context = "\n\n".join(relevant_chunks)

        if request.provider == "claude":
            answer = query_claude(request.question, context)
            model_used = "Claude 3.5 Sonnet"
        else:
            answer = query_openrouter(request.question, context)
            model_used = "GPT-4o (via OpenRouter)"

        return JSONResponse({
            "question": request.question,
            "answer": answer,
            "provider": request.provider,
            "model": model_used,
            "documents_used": doc_names,
            "chunks_used": len(relevant_chunks)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents():
    """List all uploaded documents"""
    docs = [
        {
            "doc_id": doc_id,
            "filename": doc_data["filename"],
            "size": doc_data["size"],
            "chunks": len(doc_data["chunks"])
        }
        for doc_id, doc_data in documents_store.items()
    ]
    return JSONResponse({"documents": docs, "count": len(docs)})

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document"""
    if doc_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found")

    filename = documents_store[doc_id]["filename"]
    del documents_store[doc_id]

    return JSONResponse({
        "success": True,
        "message": f"Document '{filename}' deleted successfully"
    })

@app.get("/providers")
async def get_providers():
    """Get available AI providers and their status"""
    anthropic_available = bool(os.getenv("ANTHROPIC_API_KEY"))
    openrouter_available = bool(os.getenv("OPENROUTER_KEY"))

    return JSONResponse({
        "providers": [
            {
                "name": "claude",
                "model": "Claude 3.5 Sonnet",
                "available": anthropic_available,
                "status": "✅ Ready" if anthropic_available else "❌ API key missing"
            },
            {
                "name": "openrouter",
                "model": "GPT-4o (via OpenRouter)",
                "available": openrouter_available,
                "status": "✅ Ready" if openrouter_available else "❌ API key missing"
            }
        ]
    })

@app.get("/")
async def root():
    """Serve the frontend"""
    return FileResponse("static/index.html")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse({"status": "healthy"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
