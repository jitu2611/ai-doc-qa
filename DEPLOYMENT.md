# 🚀 Deployment Guide - AI Document Q&A

This guide will help you deploy the project to GitHub and Vercel in 5 minutes.

## Prerequisites
- GitHub account: https://github.com/jitu2611
- Vercel account: https://vercel.com (free)
- Anthropic API key: https://console.anthropic.com

## Step 1: Create GitHub Repository (2 min)

### Option A: Using GitHub Web UI (Recommended)
1. Go to https://github.com/new
2. Repository name: `ai-doc-qa`
3. Description: "AI Document Q&A System with Claude AI"
4. Choose Public or Private
5. Click "Create repository"
6. Copy the "Quick setup" HTTPS URL

### Option B: Using Command Line
```bash
# Install GitHub CLI first, then:
gh auth login
gh repo create ai-doc-qa --public --description "AI Document Q&A System" --source=. --remote=origin --push
```

## Step 2: Push Code to GitHub (1 min)

After creating the repo on GitHub, run:

```bash
cd "C:\Users\jk261\OneDrive\Documents\Python Scripts\ai-doc-qa"

# Configure git (one time)
git config --global user.name "jitu2611"
git config --global user.email "your-email@github.com"

# Set remote and push
git remote add origin https://github.com/jitu2611/ai-doc-qa.git
git branch -M main
git push -u origin main
```

When prompted for password, use your **GitHub Personal Access Token**:
1. Go to https://github.com/settings/tokens/new
2. Token name: "AI Doc QA Deployment"
3. Expiration: 90 days
4. Scopes: Check `repo` (full control of repositories)
5. Click "Generate token"
6. Copy and paste when Git asks for password

## Step 3: Deploy to Vercel (2 min)

1. Go to https://vercel.com/dashboard
2. Click "New Project"
3. Click "Import Git Repository"
4. Authenticate with GitHub
5. Select `ai-doc-qa` repository
6. Click "Import"
7. **IMPORTANT**: In "Environment Variables", add:
   - Name: `ANTHROPIC_API_KEY`
   - Value: `sk-ant-v0-xxxxx...` (your Anthropic API key)
8. Click "Deploy"

Wait 2-5 minutes for Vercel to build and deploy. You'll get a live URL!

## Step 4: Test Your Deployment

Once Vercel finishes:
1. Click the deployment URL
2. Upload a sample PDF
3. Ask a question about the PDF
4. Verify it works!

## Local Testing (Optional)

Before deploying, test locally:

```bash
cd "C:\Users\jk261\OneDrive\Documents\Python Scripts\ai-doc-qa"

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the app
uvicorn main:app --reload

# Visit http://localhost:8000
```

## Troubleshooting

**Git push fails:**
- Make sure you have a GitHub Personal Access Token (not password)
- Token must have `repo` scope
- Run: `git remote -v` to verify the remote URL

**Vercel deployment fails:**
- Check that ANTHROPIC_API_KEY environment variable is set
- View logs in Vercel dashboard
- Ensure all files are pushed to GitHub

**App not working:**
- Check your Anthropic API key is valid
- Upload a valid PDF first
- Check browser console for errors

## What's Deployed

✅ FastAPI backend  
✅ Beautiful web UI  
✅ PDF upload & processing  
✅ AI-powered Q&A  
✅ Document management  
✅ RAG (Retrieval-Augmented Generation)  

Enjoy your AI Document Q&A System! 🎉
