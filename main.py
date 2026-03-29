import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import PyPDF2
from anthropic import Anthropic
from pydantic import BaseModel
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import re

app = FastAPI(title="AI Document Q&A System")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Anthropic client
client = Anthropic()

# In-memory storage for documents and embeddings
documents_store = {}
vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
document_vectors = None

class QueryRequest(BaseModel):
    question: str

class DocumentChunk(BaseModel):
    filename: str
    content: str

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

@app.post("/query")
async def query_document(request: QueryRequest):
    """Query uploaded documents using AI"""
    if not documents_store:
        raise HTTPException(status_code=400, detail="No documents uploaded. Please upload a document first.")

    try:
        # Collect all chunks from all documents
        all_chunks = []
        doc_names = []
        for doc_id, doc_data in documents_store.items():
            all_chunks.extend(doc_data["chunks"])
            doc_names.append(doc_data["filename"])

        # Find relevant chunks
        relevant_chunks = find_relevant_chunks(request.question, all_chunks, top_k=5)
        context = "\n\n".join(relevant_chunks)

        # Prepare prompt for Claude
        system_prompt = """You are a helpful AI assistant specialized in answering questions about uploaded documents.
Use the provided document content to answer questions accurately. If the answer is not found in the documents,
clearly state that the information is not available in the provided documents."""

        user_message = f"""Question: {request.question}

Relevant document content:
{context}

Please answer the question based on the provided document content."""

        # Query Claude API
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        answer = response.content[0].text

        return JSONResponse({
            "question": request.question,
            "answer": answer,
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
