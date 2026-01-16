# Local Development Guide

Quick guide for running the full stack locally and rebuilding FAISS when content changes.

---

## Part 1: Rebuild FAISS Vectorstore

**When to rebuild**: After adding/editing blog posts, projects, or experiences in `src/content/`.

### Step 1: Activate Python Environment

```bash
cd /Users/crombie/tcheiner/tcheiner-astro-bento

# Activate virtual environment (venv is in parent of backend)
source .venv/bin/activate

# Verify activation (should show .venv in path)
which python
```

### Step 2: Rebuild FAISS Index

```bash
cd backend

# Rebuild vectorstore (reads from ../src/content/)
python -c "from chatbot.services import rebuild_vectorstore; rebuild_vectorstore()"
```

**Expected Output**:
```
Embedding X new/updated documents...
# Or: "No new or updated documents to embed."
```

**Result**: Updates `backend/chatbot/faiss_index/`:
- `index.faiss` - FAISS similarity search index
- `index.pkl` - Document metadata and chunks

### Step 3: Verify FAISS Index

```bash
# Check files exist and see size
ls -lh chatbot/faiss_index/

# Should see:
# index.faiss (~750KB)
# index.pkl (~560KB)
```

---

## Part 2: Run Backend Locally

### Step 1: Ensure Environment Variables

```bash
cd /Users/crombie/tcheiner/tcheiner-astro-bento/backend

# Check .env exists
cat .env

# Should contain:
# OPENAI_API_KEY=sk-...
# ALLOWED_ORIGINS=http://localhost:4321,...
```

If missing, create it:
```bash
cat > .env << 'EOF'
OPENAI_API_KEY=sk-your-actual-key-here
ALLOWED_ORIGINS=http://localhost:4321,https://localhost:4321,https://tcheiner.com,https://www.tcheiner.com
RETRIEVAL_K=5
SCORE_THRESHOLD=0.5
MAX_TOKENS=600
RETRIEVAL_STRATEGY=default
EOF
```

### Step 2: Start Backend Server

```bash
cd /Users/crombie/tcheiner/tcheiner-astro-bento/backend

# Make sure venv is activated
source ../.venv/bin/activate

# Start FastAPI with hot reload
uvicorn chatbot.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
TC Heiner Chatbot is starting up...
INFO:     Application startup complete.
```

### Step 3: Test Backend Endpoints

Open a **new terminal** (keep backend running in first terminal):

```bash
# Health check
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Root endpoint
curl http://localhost:8000/
# Expected: {"status":"TC Heiner Chatbot API","version":"1.0.0"}

# Test chatbot
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Tell me about TC Heiner"}'

# Should return JSON with:
# {"answer": "...", "sources": ["..."]}
```

**Backend is now running on**: http://localhost:8000

---

## Part 3: Run Frontend Locally

### Step 1: Ensure Environment Variables

```bash
cd /Users/crombie/tcheiner/tcheiner-astro-bento

# Check/create .env
cat .env
```

If missing or incorrect, create/update:
```bash
cat > .env << 'EOF'
# Point to LOCAL backend
PUBLIC_CHATBOT_API_URL=http://localhost:8000/ask

# Or point to PRODUCTION backend for testing
# PUBLIC_CHATBOT_API_URL=https://5f3ysv93x1.execute-api.us-east-1.amazonaws.com/prod/ask
EOF
```

### Step 2: Install Dependencies (if needed)

```bash
cd /Users/crombie/tcheiner/tcheiner-astro-bento

# Check package manager (using pnpm per package.json)
which pnpm

# Install if needed
npm install -g pnpm

# Install dependencies
pnpm install
```

### Step 3: Start Frontend Dev Server

```bash
cd /Users/crombie/tcheiner/tcheiner-astro-bento

# Start Astro dev server
npm run dev

# Or using pnpm
pnpm dev
```

**Expected Output**:
```
 astro  v5.13.5 ready in XXX ms

┃ Local    http://localhost:4321/
┃ Network  use --host to expose

watching for file changes...
```

### Step 4: Test Frontend

1. **Open browser**: http://localhost:4321
2. **Click chatbot** (💬 Chat button bottom-right)
3. **Ask a question**: "Tell me about TC Heiner"
4. **Verify**:
   - Chatbot opens
   - Question sends
   - Response appears (may take 5-10 seconds)
   - Sources linked at bottom
   - Free questions counter shows (5/5 remaining)

---

## Full Local Stack Summary

**Backend (Terminal 1)**:
```bash
cd /Users/crombie/tcheiner/tcheiner-astro-bento/backend
source ../.venv/bin/activate
uvicorn chatbot.main:app --reload --port 8000
```
Running on: http://localhost:8000

**Frontend (Terminal 2)**:
```bash
cd /Users/crombie/tcheiner/tcheiner-astro-bento
npm run dev
```
Running on: http://localhost:4321

---

## Common Workflows

### Workflow 1: Content Update (Add Blog Post)

```bash
# 1. Edit content
vim src/content/posts/new-post.mdx

# 2. Rebuild FAISS
cd backend
source ../.venv/bin/activate
python -c "from chatbot.services import rebuild_vectorstore; rebuild_vectorstore()"

# 3. Backend auto-reloads (if running with --reload)
# No restart needed!

# 4. Test in browser
# Ask chatbot about new content
```

### Workflow 2: Backend Code Changes

```bash
# 1. Edit backend code
vim backend/chatbot/main.py

# 2. Backend auto-reloads (uvicorn --reload)
# Check terminal for reload message

# 3. Test immediately in browser
```

### Workflow 3: Frontend Code Changes

```bash
# 1. Edit frontend code
vim src/components/ChatbotUI.tsx

# 2. Frontend auto-reloads (Astro HMR)
# Browser refreshes automatically

# 3. Changes appear immediately
```

### Workflow 4: Test Improved Chatbot Locally

```bash
# Backend should already be running with new prompt
# (changes already in code from feature branch)

# Test strategic positioning:
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Tell me about your leadership experience"}'

# Should see conversational response that connects experiences
```

---

## Troubleshooting

### Error: "FAISS index not found"

```bash
# Rebuild it
cd backend
source ../.venv/bin/activate
python -c "from chatbot.services import rebuild_vectorstore; rebuild_vectorstore()"
```

### Error: "OpenAI API key not found"

```bash
# Check backend/.env
cat backend/.env | grep OPENAI_API_KEY

# If missing, add it:
echo 'OPENAI_API_KEY=sk-your-key-here' >> backend/.env
```

### Error: "Module not found" (Python)

```bash
# Reinstall dependencies
cd backend
source ../.venv/bin/activate
pip install -r requirements-clean.txt
```

### Error: "Cannot find module" (Frontend)

```bash
# Reinstall node modules
cd /Users/crombie/tcheiner/tcheiner-astro-bento
rm -rf node_modules
pnpm install
```

### Backend Not Loading Updated Prompt

```bash
# Force restart backend
# CTRL+C in backend terminal
# Then restart:
uvicorn chatbot.main:app --reload --port 8000
```

### Chatbot Shows Old Responses

```bash
# Clear browser cache or open incognito
# Or hard refresh: Cmd+Shift+R (Mac) / Ctrl+Shift+R (Windows)
```

### CORS Error in Browser Console

```bash
# Check backend CORS includes localhost:4321
# backend/chatbot/main.py line 133-140

# Should have:
allow_origins=["http://localhost:4321", ...]
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Activate venv | `source .venv/bin/activate` |
| Rebuild FAISS | `cd backend && python -c "from chatbot.services import rebuild_vectorstore; rebuild_vectorstore()"` |
| Start backend | `cd backend && uvicorn chatbot.main:app --reload --port 8000` |
| Start frontend | `npm run dev` |
| Test backend | `curl http://localhost:8000/health` |
| View frontend | `http://localhost:4321` |
| Stop servers | `CTRL+C` in each terminal |

---

## Production Testing

To test against production backend locally:

```bash
# Update .env
PUBLIC_CHATBOT_API_URL=https://5f3ysv93x1.execute-api.us-east-1.amazonaws.com/prod/ask

# Restart frontend
# CTRL+C then npm run dev

# Frontend now uses production backend
# Good for testing frontend changes without running backend
```

---

## Next Steps

1. ✅ Run backend locally (this guide)
2. ✅ Run frontend locally (this guide)
3. ✅ Test improved chatbot responses
4. 🔄 Make adjustments to prompt if needed
5. 🔄 Test with various questions (leadership, technical skills, projects)
6. 🚀 When satisfied, deploy (see DEPLOYMENT_GUIDE.md)
