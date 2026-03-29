# AI Document Q&A System 📚

A modern, intelligent document analyzer powered by Claude AI and FastAPI. Upload PDF documents and ask natural language questions to get AI-powered answers based on your document content.

## ✨ Features

- **PDF Upload**: Drag-and-drop interface for uploading PDF documents
- **Smart Q&A**: Ask questions and get intelligent answers based on document content
- **RAG System**: Uses Retrieval-Augmented Generation with TF-IDF for relevant chunk selection
- **Multiple Documents**: Manage and query across multiple uploaded documents
- **Real-time Processing**: Fast responses powered by Claude 3.5 Sonnet
- **Beautiful UI**: Modern, responsive web interface with gradient design
- **RESTful API**: Clean API endpoints for integration

## 🚀 Tech Stack

- **Backend**: FastAPI (Python)
- **AI**: Anthropic Claude API (Claude 3.5 Sonnet)
- **Vector Search**: scikit-learn TF-IDF for semantic search
- **PDF Processing**: PyPDF2
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Deployment**: Vercel

## 📁 Project Structure

```
ai-doc-qa/
├── main.py                 # FastAPI application & API routes
├── static/
│   └── index.html         # Web UI (beautiful responsive interface)
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── vercel.json            # Vercel deployment configuration
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## 🏃 Getting Started

### Prerequisites

- Python 3.8+
- pip
- Anthropic API key (get from console.anthropic.com)

### Local Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

4. **Run locally**
   ```bash
   uvicorn main:app --reload
   ```

5. **Visit** http://localhost:8000

## 🤖 Recent AI Trends Demonstrated

- **Retrieval-Augmented Generation (RAG)**
- **Claude 3.5 Sonnet Integration**
- **Semantic Search with TF-IDF**
- **Real-time AI Responses**
- **Multi-Document Processing**

## 🚀 Deploy on Vercel

1. Push to GitHub
2. Visit vercel.com and import the repository
3. Add ANTHROPIC_API_KEY environment variable
4. Deploy!

## 📄 License

MIT License
