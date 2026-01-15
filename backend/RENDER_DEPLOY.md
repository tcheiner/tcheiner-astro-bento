# Deploying TC Heiner Chatbot to Render

This guide walks through deploying your FastAPI chatbot to Render (replacing AWS Lambda).

## Why Render vs AWS Lambda?

| Feature | AWS Lambda | Render |
|---------|-----------|--------|
| Setup Complexity | High (Terraform, ECR, Mangum) | Low (Git push) |
| Cold Starts | Yes (container images) | Minimal (always-on) |
| Cost | Pay per request | $7/month (starter) or free tier |
| Management | Manual container builds | Auto-deploy on git push |
| Debugging | CloudWatch logs | Real-time logs in dashboard |

## Prerequisites

1. Render account (free): https://render.com
2. GitHub repository with your code
3. OpenAI API key

## Option 1: Deploy via Blueprint (Recommended)

The `render.yaml` file already exists in the backend directory.

### Steps:

1. **Push code to GitHub**
   ```bash
   cd /Users/crombie/tcheiner/tcheiner-astro-bento
   git add backend/render.yaml backend/chatbot/main.py
   git commit -m "Add Render deployment configuration"
   git push
   ```

2. **Create New Blueprint in Render**
   - Go to https://dashboard.render.com/blueprints
   - Click "New Blueprint Instance"
   - Connect your GitHub repository
   - Render will detect `render.yaml` automatically
   - Select the branch (usually `main`)

3. **Configure Environment Variables**
   - In the Blueprint setup, set:
     - `OPENAI_API_KEY`: Your OpenAI API key
   - Other env vars are already configured in `render.yaml`

4. **Deploy**
   - Click "Apply" to create the service
   - Render will build and deploy automatically
   - Build time: ~5-10 minutes (first deployment)

5. **Get Your Service URL**
   - After deployment completes, you'll get a URL like:
     `https://tcheiner-chatbot.onrender.com`

## Option 2: Manual Deployment (Dashboard)

If you prefer manual setup:

1. **Go to Render Dashboard**: https://dashboard.render.com

2. **New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select `backend` directory as root

3. **Configure Service**
   ```
   Name: tcheiner-chatbot
   Region: Oregon (or your choice)
   Branch: main
   Root Directory: backend
   Runtime: Python 3
   Build Command: pip install -r requirements-clean.txt
   Start Command: uvicorn chatbot.main:app --host 0.0.0.0 --port $PORT
   ```

4. **Set Environment Variables**
   ```
   OPENAI_API_KEY=sk-your-key-here
   ALLOWED_ORIGINS=http://localhost:4321,https://localhost:4321,https://tcheiner.com,https://www.tcheiner.com
   MAX_TOKENS=600
   RETRIEVAL_K=5
   SCORE_THRESHOLD=0.5
   RETRIEVAL_STRATEGY=default
   ```

5. **Choose Plan**
   - **Free Tier**: Service spins down after 15 min inactivity (cold starts)
   - **Starter ($7/mo)**: Always-on, better performance (recommended)

6. **Deploy**
   - Click "Create Web Service"
   - Wait for build to complete

## After Deployment

### 1. Update CORS Origins

Once deployed, get your Render URL and update CORS:

```python
# backend/chatbot/main.py line 133
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4321",
        "https://localhost:4321",
        "https://tcheiner.com",
        "https://www.tcheiner.com",
        "https://tcheiner-chatbot.onrender.com"  # Add your Render URL
    ],
    ...
)
```

Commit and push - Render will auto-redeploy.

### 2. Update Frontend API URL

Update your frontend to point to the new Render URL:

```typescript
// src/components/ChatbotUI.tsx
const API_URL = "https://tcheiner-chatbot.onrender.com/ask";
```

### 3. Test the Deployment

```bash
# Health check
curl https://tcheiner-chatbot.onrender.com/health

# Test chatbot
curl -X POST "https://tcheiner-chatbot.onrender.com/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Tell me about TC"}'
```

## Rebuild FAISS Index

**IMPORTANT**: After any content changes to your blog/portfolio:

```bash
cd backend
source ../.venv/bin/activate
python -c "from chatbot.services import rebuild_vectorstore; rebuild_vectorstore()"
git add chatbot/faiss_index/
git commit -m "Update FAISS vectorstore with latest content"
git push
```

Render will auto-redeploy with updated content.

## Monitoring & Logs

- **Logs**: https://dashboard.render.com → Your Service → Logs tab
- **Metrics**: View CPU, memory, and request metrics in dashboard
- **Health Check**: Render automatically pings `/health` every few minutes

## Cost Comparison

### AWS Lambda (Current)
- ECR storage: ~$1/month
- Lambda invocations: $0.20 per 1M requests
- Data transfer: Variable
- **Total**: ~$2-5/month (low traffic)

### Render
- Free Tier: $0 (spins down after 15 min)
- Starter: $7/month (always-on, 512MB RAM)
- Standard: $25/month (better specs)

**Recommendation**: Start with Starter plan ($7/mo) for consistent performance.

## Troubleshooting

### Build Fails
- Check `requirements-clean.txt` has all dependencies
- Review build logs in Render dashboard
- Ensure Python version matches (3.12)

### 502 Bad Gateway
- Check start command is correct: `uvicorn chatbot.main:app --host 0.0.0.0 --port $PORT`
- Verify FAISS index exists in `chatbot/faiss_index/`
- Check environment variables are set

### CORS Errors
- Verify Render URL is in CORS `allow_origins`
- Check frontend API URL matches Render deployment URL

### Slow Responses (Free Tier)
- Free tier spins down after 15 min inactivity
- First request after sleep takes ~30 seconds
- Upgrade to Starter plan for always-on service

## Rollback to AWS Lambda

If needed, the AWS Lambda deployment still works:

```bash
cd backend
./build-container.sh
cd terraform
tofu apply
```

## Next Steps

1. ✅ Deploy to Render
2. ✅ Update CORS origins
3. ✅ Update frontend API URL
4. Test all chatbot functionality
5. Monitor logs for errors
6. Consider upgrading to Starter plan for better UX

---

**Questions?** Check Render docs: https://render.com/docs
