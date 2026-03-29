#!/bin/bash
set -e

echo "🚀 AI Document Q&A - Deployment Script"
echo "========================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Verify git status
echo -e "${BLUE}[1/4] Checking git status...${NC}"
if [ -z "$(git remote get-url origin)" ]; then
    echo "Setting up GitHub remote..."
    read -p "Enter your GitHub username [jitu2611]: " GITHUB_USER
    GITHUB_USER=${GITHUB_USER:-jitu2611}
    git remote add origin "https://github.com/$GITHUB_USER/ai-doc-qa.git"
fi
echo -e "${GREEN}✓ Git configured${NC}"

# Step 2: Verify dependencies
echo -e "${BLUE}[2/4] Checking Python dependencies...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    exit 1
fi
echo -e "${GREEN}✓ Python found${NC}"

# Step 3: Show environment setup
echo -e "${BLUE}[3/4] Environment setup${NC}"
echo "Create .env file with:"
echo "  ANTHROPIC_API_KEY=sk-ant-your-key-here"
echo -e "${GREEN}✓ Ready to configure${NC}"

# Step 4: Push to GitHub
echo -e "${BLUE}[4/4] Pushing to GitHub...${NC}"
git branch -M main
git push -u origin main
echo -e "${GREEN}✓ Pushed to GitHub${NC}"

echo ""
echo -e "${GREEN}✅ All steps completed!${NC}"
echo ""
echo "Next steps:"
echo "1. Go to: https://vercel.com"
echo "2. Click: New Project"
echo "3. Import your GitHub repository"
echo "4. Add ANTHROPIC_API_KEY environment variable"
echo "5. Deploy!"
echo ""
echo "Or run locally:"
echo "  pip install -r requirements.txt"
echo "  cp .env.example .env"
echo "  # Edit .env with your API key"
echo "  uvicorn main:app --reload"
