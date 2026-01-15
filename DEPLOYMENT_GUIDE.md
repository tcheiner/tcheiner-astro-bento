# Complete Deployment Guide: Netlify + Render

This guide provides step-by-step instructions to deploy your entire TC Heiner portfolio with AI chatbot.

**Target Architecture:**
- 🎨 **Frontend (Astro)**: Netlify
- 🤖 **Backend (FastAPI)**: Render
- 🧠 **Vectorstore (FAISS)**: Bundled with backend in Git

---

## Prerequisites

- ✅ GitHub repository: `tcheiner/tcheiner-astro-bento`
- ✅ Netlify account (free): https://netlify.com
- ✅ Render account (free/starter): https://render.com
- ✅ OpenAI API key
- ✅ Domain (optional): `tcheiner.com`

---

## Part 1: Deploy Backend to Render (First!)

Deploy the chatbot API backend first so you have the URL for the frontend.

### Step 1.1: Push Code to GitHub

```bash
cd /Users/crombie/tcheiner/tcheiner-astro-bento

# Make sure you're on the feature branch
git checkout feature/humanize-chatbot-responses

# Verify FAISS index is committed
git status backend/chatbot/faiss_index/

# Push to GitHub
git push -u origin feature/humanize-chatbot-responses
```

### Step 1.2: Deploy to Render via Blueprint

1. **Go to Render Dashboard**: https://dashboard.render.com/blueprints

2. **Create New Blueprint Instance**:
   - Click "New Blueprint Instance"
   - Connect your GitHub account if not already connected
   - Select repository: `tcheiner/tcheiner-astro-bento`
   - Select branch: `feature/humanize-chatbot-responses`
   - Render will detect `backend/render.yaml`

3. **Configure Service**:
   - Service name: `tcheiner-chatbot` (or your choice)
   - Region: `Oregon` (or closest to your users)
   - Plan: **Starter ($7/mo)** recommended for production
     - Free tier available but spins down after 15 min inactivity
     - Starter keeps service always-on for instant responses

4. **Set Environment Variables**:
   ```
   OPENAI_API_KEY=sk-your-actual-openai-key-here
   ```
   - Other variables are pre-configured in `render.yaml`
   - DO NOT commit API keys to git

5. **Deploy**:
   - Click "Apply" to create the service
   - Build will take ~5-10 minutes
   - Watch logs for any errors

6. **Get Your Backend URL**:
   - After successful deployment, copy your service URL:
   - Example: `https://tcheiner-chatbot.onrender.com`
   - **Save this URL** - you need it for frontend configuration!

### Step 1.3: Verify Backend Works

Test the deployed backend:

```bash
# Health check
curl https://tcheiner-chatbot.onrender.com/health

# Test chatbot (should return JSON response)
curl -X POST "https://tcheiner-chatbot.onrender.com/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Tell me about TC Heiner"}'
```

**Expected Response**: JSON with `answer` and `sources` fields.

---

## Part 2: Deploy Frontend to Netlify

### Step 2.1: Update Frontend API URL

**IMPORTANT**: Before deploying frontend, set the backend URL you got from Render.

1. **Create `.env` file in root** (if not exists):
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and set your Render backend URL**:
   ```bash
   # .env
   PUBLIC_CHATBOT_API_URL=https://tcheiner-chatbot.onrender.com/ask
   ```

3. **DO NOT commit `.env`** (already in `.gitignore`)

### Step 2.2: Deploy to Netlify

**Option A: Netlify Dashboard (Recommended)**

1. **Go to Netlify**: https://app.netlify.com

2. **New Site from Git**:
   - Click "Add new site" → "Import an existing project"
   - Choose "GitHub"
   - Select repository: `tcheiner/tcheiner-astro-bento`
   - Select branch: `feature/humanize-chatbot-responses` (or `main` after merge)

3. **Configure Build Settings**:
   - Netlify auto-detects from `netlify.toml`:
     - Build command: `npm run build`
     - Publish directory: `dist`
     - Node version: 20
   - Click "Show advanced" → "New variable"

4. **Set Environment Variable**:
   ```
   Key: PUBLIC_CHATBOT_API_URL
   Value: https://tcheiner-chatbot.onrender.com/ask
   ```
   (Use your actual Render URL from Step 1.6)

5. **Deploy**:
   - Click "Deploy site"
   - Build takes ~2-3 minutes
   - Netlify provides a temporary URL like `https://random-name-123.netlify.app`

6. **Custom Domain (Optional)**:
   - In site settings → Domain management
   - Add custom domain: `tcheiner.com`
   - Follow DNS configuration instructions
   - Netlify provides free SSL certificate

**Option B: Netlify CLI**

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Deploy from root directory
cd /Users/crombie/tcheiner/tcheiner-astro-bento
netlify deploy --prod

# Follow prompts:
# - Link to existing site or create new
# - Build command: npm run build
# - Publish directory: dist

# Set environment variable via CLI
netlify env:set PUBLIC_CHATBOT_API_URL "https://tcheiner-chatbot.onrender.com/ask"
```

### Step 2.3: Verify Frontend Works

1. **Open your Netlify site**: `https://tcheiner.netlify.app` or `https://tcheiner.com`
2. **Click the chatbot icon** (💬 Chat button in bottom-right)
3. **Ask a question**: "Tell me about TC Heiner"
4. **Verify**:
   - Chatbot opens and shows welcome message
   - Question sends successfully
   - Response appears (may take 5-10s first time if Render free tier)
   - Sources are linked at bottom of response

---

## Part 3: Final Configuration

### Step 3.1: Update CORS (if needed)

If you used a custom Netlify domain, update CORS:

1. **Edit `backend/chatbot/main.py`** (line 133-140):
   ```python
   allow_origins=[
       "http://localhost:4321",
       "https://localhost:4321",
       "https://tcheiner.com",
       "https://www.tcheiner.com",
       "https://tcheiner.netlify.app",
       "https://your-custom-domain.com",  # Add your domain
   ],
   ```

2. **Commit and push**:
   ```bash
   git add backend/chatbot/main.py
   git commit -m "Add custom domain to CORS"
   git push
   ```

3. **Render auto-deploys** on git push (if connected to GitHub)

### Step 3.2: Merge to Main Branch

Once everything works on the feature branch:

```bash
# Create pull request on GitHub
gh pr create --title "Humanize chatbot + Netlify/Render deployment" \
  --body "See DEPLOYMENT_GUIDE.md for details"

# Or manually:
# 1. Go to GitHub
# 2. Create PR from feature/humanize-chatbot-responses to main
# 3. Review and merge

# After merge, both Netlify and Render will deploy from main branch
```

---

## Updating Content (Important!)

### When You Add/Edit Blog Posts, Projects, or Experiences:

The FAISS vectorstore needs rebuilding for the chatbot to know about new content.

**Process:**

1. **Edit your MDX files** in `src/content/`

2. **Rebuild FAISS vectorstore**:
   ```bash
   cd backend
   source ../.venv/bin/activate
   python -c "from chatbot.services import rebuild_vectorstore; rebuild_vectorstore()"
   ```

3. **Commit updated vectorstore**:
   ```bash
   git add backend/chatbot/faiss_index/
   git commit -m "Update FAISS vectorstore with latest content"
   git push
   ```

4. **Automatic redeploy**:
   - Render detects the commit and rebuilds the backend
   - Chatbot now has updated knowledge
   - No frontend changes needed

**Important**: FAISS index is now **committed to git** (1.3MB). This enables Render to have the vectorstore without external storage.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         USER BROWSER                         │
│              https://tcheiner.com (Netlify)                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ POST /ask {"question": "..."}
                      │ PUBLIC_CHATBOT_API_URL env var
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              CHATBOT API (Render)                            │
│        https://tcheiner-chatbot.onrender.com                 │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │  FastAPI + LangChain + GPT-4o-mini               │      │
│  │  • Content filtering                              │      │
│  │  • FAISS similarity search (k=5)                  │      │
│  │  • Strategic positioning prompt                   │      │
│  │  • Temperature: 0.6                               │      │
│  │  • Max tokens: 600                                │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │  FAISS Vectorstore (1.3MB)                       │      │
│  │  Bundled in git repository                        │      │
│  │  backend/chatbot/faiss_index/                     │      │
│  │  • index.faiss (750KB)                            │      │
│  │  • index.pkl (560KB)                              │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                      │
                      │ OpenAI API calls
                      ▼
                  OpenAI GPT-4o-mini
```

---

## Cost Breakdown

### Monthly Costs

| Service | Plan | Cost | Notes |
|---------|------|------|-------|
| Netlify | Starter | **$0** | 100GB bandwidth, auto-scaling |
| Render Backend | Starter | **$7** | Always-on, 512MB RAM |
| Render Backend | Free | **$0** | Spins down after 15 min |
| OpenAI API | Pay-per-use | **~$2-5** | GPT-4o-mini (5-10k queries/mo) |
| **Total** | | **$7-12/mo** | With Render Starter plan |

**Recommendation**: Use Render **Starter plan** ($7/mo) for production:
- Always-on service (no cold starts)
- Better user experience (instant responses)
- 512MB RAM (sufficient for FAISS + FastAPI)

---

## Troubleshooting

### Backend Issues

**Error: "FAISS index not found"**
- Solution: FAISS index must be committed to git
- Check: `git ls-files backend/chatbot/faiss_index/`
- Should see: `index.faiss`, `index.pkl`

**Error: "OpenAI API key not found"**
- Solution: Set `OPENAI_API_KEY` in Render dashboard
- Navigate to: Service → Environment → Add Environment Variable

**Error: CORS policy blocking requests**
- Solution: Add your domain to CORS in `backend/chatbot/main.py`
- Redeploy after committing change

### Frontend Issues

**Chatbot not appearing**
- Check browser console for errors
- Verify `PUBLIC_CHATBOT_API_URL` is set in Netlify environment variables

**"Sorry, I encountered an error"**
- Check Render logs: Dashboard → Service → Logs
- Verify backend is running: `curl https://your-backend.onrender.com/health`
- Check CORS configuration includes your Netlify domain

**Slow responses (15-30 seconds)**
- Likely using Render free tier (cold starts)
- Solution: Upgrade to Render Starter plan ($7/mo)

### Content Update Issues

**Chatbot doesn't know about new blog posts**
- Rebuild FAISS: `python -c "from chatbot.services import rebuild_vectorstore; rebuild_vectorstore()"`
- Commit and push: `git add backend/chatbot/faiss_index/ && git commit -m "Update vectorstore" && git push`
- Wait for Render to redeploy (~2-3 min)

---

## Monitoring & Maintenance

### Netlify Dashboard
- **Deploys**: View build logs and deploy history
- **Analytics**: Page views, bandwidth usage (paid feature)
- **Functions**: None used (static site)

### Render Dashboard
- **Logs**: Real-time logs for debugging
- **Metrics**: CPU, memory, request count
- **Events**: Deploy history and manual deploys
- **Health**: Auto-monitoring via `/health` endpoint

### OpenAI Usage
- **Dashboard**: https://platform.openai.com/usage
- Monitor API calls and costs
- Set usage limits if needed

---

## Rollback Plan

### If Deployment Fails

**Rollback Frontend (Netlify)**:
1. Go to Netlify → Deploys
2. Find last working deploy
3. Click "Publish deploy"
4. Instant rollback (no rebuild)

**Rollback Backend (Render)**:
1. Revert git commits: `git revert HEAD`
2. Push to trigger redeploy
3. Or use Render dashboard: Service → "Rollback to..."

### Emergency: Revert to AWS Lambda

If Render doesn't work, you can revert to AWS Lambda:

```bash
cd backend
./build-container.sh
cd terraform
tofu apply
```

Update frontend `PUBLIC_CHATBOT_API_URL` back to Lambda endpoint.

---

## Next Steps

1. ✅ Deploy backend to Render
2. ✅ Get backend URL
3. ✅ Deploy frontend to Netlify
4. ✅ Configure environment variables
5. ✅ Test chatbot functionality
6. ✅ Set up custom domain (optional)
7. ✅ Monitor for first 24-48 hours
8. ⏭️ Consider Render Starter plan if using free tier

---

## Additional Resources

- **Netlify Docs**: https://docs.netlify.com
- **Render Docs**: https://render.com/docs
- **Astro Docs**: https://docs.astro.build
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **OpenAI API**: https://platform.openai.com/docs

For issues, check:
- `backend/RENDER_DEPLOY.md` - Detailed Render configuration
- `backend/DEPLOYMENT_OVERVIEW.md` - Architecture deep-dive
- GitHub Issues: https://github.com/tcheiner/tcheiner-astro-bento/issues
