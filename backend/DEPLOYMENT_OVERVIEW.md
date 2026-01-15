# TC Heiner Portfolio - Current Deployment Architecture

## Frontend (UI) Deployment

### Platform: Vercel (inferred from `.vercel` in .gitignore)
- **Framework**: Astro static site
- **Domain**: https://tcheiner.com
- **Source**: GitHub repository `tcheiner/tcheiner-astro-bento`
- **Build Command**: `npm run build` (generates `/dist`)
- **Deploy**: Automatic on git push to main branch

### Frontend Components:
- **Astro pages**: Static site generation
- **React components**: Including `ChatbotUI.tsx` for AI chatbot interface
- **MDX content**: Blog posts, projects, experiences, books, recipes
- **Styling**: Tailwind CSS + shadcn/ui components

## Backend (Chatbot API) Deployment

### Platform: AWS Lambda + API Gateway
- **Runtime**: Python 3.12 container image
- **Container Registry**: AWS ECR (Elastic Container Registry)
- **Infrastructure**: Managed by Terraform/OpenTofu
- **Region**: us-east-1
- **API Endpoint**: https://5f3ysv93x1.execute-api.us-east-1.amazonaws.com/prod/ask

### Deployment Process:
```bash
cd backend
./build-container.sh   # Builds Docker image, pushes to ECR
cd terraform
tofu apply            # Updates Lambda function
```

### Lambda Configuration:
- **Memory**: 512MB
- **Timeout**: 15 minutes
- **Architecture**: ARM64
- **Handler**: `chatbot.main.handler` (via Mangum wrapper)

## FAISS Vectorstore Hosting

### Current Strategy: Bundled with Lambda Container

**Storage Location**: `backend/chatbot/faiss_index/`
- `index.faiss` - FAISS similarity search index (750KB)
- `index.pkl` - Metadata and document chunks (560KB)
- **Total Size**: ~1.3MB

### How It Works:

1. **Local Development**:
   - FAISS index stored in `backend/chatbot/faiss_index/`
   - NOT tracked in git (too large, generated artifact)
   - Rebuilt locally when content changes

2. **Production Deployment**:
   ```dockerfile
   # Dockerfile line 14
   COPY chatbot/faiss_index/ ./chatbot/faiss_index/
   ```
   - FAISS index **bundled INTO the Docker container**
   - Deployed as part of the Lambda container image
   - Loaded from container filesystem at runtime

3. **Update Process** (CRITICAL):
   ```bash
   # After adding/editing blog posts, projects, or experiences:
   cd backend
   python -c "from chatbot.services import rebuild_vectorstore; rebuild_vectorstore()"
   # This regenerates faiss_index/ locally

   # Then rebuild and redeploy container:
   ./build-container.sh   # Bundles new index into container
   cd terraform && tofu apply
   ```

### Key Implications:

#### ✅ Advantages:
- No external storage needed (S3, etc.)
- Fast loading (local filesystem)
- Simple deployment (single artifact)
- No cold start latency for vectorstore

#### ⚠️ Limitations:
- **Manual rebuild required** after content changes
- FAISS index NOT automatically synced with website content
- Must rebuild container to update chatbot knowledge
- 10GB container size limit (current: ~1.3MB used, plenty of room)

#### 🔄 Workflow:
```
Content Change → Rebuild FAISS → Rebuild Container → Deploy Lambda
     (MDX)           (Python)      (Docker)           (Terraform)
```

## API Key Management

### Development:
- Stored in `backend/.env` (gitignored)
- Loaded via `python-dotenv`

### Production (Lambda):
- **AWS SSM Parameter Store**: `/myapp/OPENAI_API_KEY`
- Retrieved at runtime via boto3
- Encrypted at rest
- No secrets in code or environment variables

## Migration to Render: Key Changes Needed

### 1. Vectorstore Strategy:

**Current (Lambda)**: Bundled in container ✅
**Render Options**:
- **Option A (Recommended)**: Same as Lambda - commit FAISS index to git
  - Pros: Simple, no external storage
  - Cons: 1.3MB added to repo (acceptable)
  - Implementation: Remove `faiss_index/` from gitignore

- **Option B**: External storage (S3/R2)
  - Pros: Keeps git repo small
  - Cons: Adds complexity, cold start latency
  - Implementation: Load from S3 at startup

- **Option C**: Rebuild on deployment
  - Pros: Always fresh
  - Cons: Adds ~2 min to build time, needs content access
  - Implementation: Add rebuild step to Render build command

### 2. Frontend API URL:

**Current**: `https://5f3ysv93x1.execute-api.us-east-1.amazonaws.com/prod/ask`
**New**: `https://tcheiner-chatbot.onrender.com/ask`

Update in: `src/components/ChatbotUI.tsx`

### 3. CORS Origins:

Must add Render URL to allowed origins:
```python
# backend/chatbot/main.py
allow_origins=[
    "http://localhost:4321",
    "https://tcheiner.com",
    "https://www.tcheiner.com",
    "https://tcheiner-chatbot.onrender.com"  # Add this
]
```

### 4. Environment Variables:

**Current (Lambda)**: SSM Parameter Store
**New (Render)**: Render dashboard environment variables

Same variables needed:
- `OPENAI_API_KEY`
- `ALLOWED_ORIGINS`
- `MAX_TOKENS`
- `RETRIEVAL_K`
- `SCORE_THRESHOLD`

## Recommended: Commit FAISS Index to Git

Given the small size (1.3MB), the simplest approach is:

```bash
# Remove faiss_index from gitignore
cd backend
git add chatbot/faiss_index/
git commit -m "Add FAISS vectorstore for deployment"
```

**Benefits**:
- Works identically on Lambda and Render
- No external storage dependencies
- Deterministic deployments
- Simple rollback (git revert)

**Trade-off**: 1.3MB added to repo (negligible for modern git)

## Cost Comparison

### Current (AWS Lambda):
- **Lambda**: ~$0.20 per 1M requests
- **ECR Storage**: ~$1/month
- **API Gateway**: ~$3.50 per million requests
- **SSM**: Free (< 10k API calls)
- **Estimated**: $2-5/month (low traffic)

### Proposed (Render):
- **Starter Plan**: $7/month (always-on)
- **Free Plan**: $0 (spins down after 15 min)
- **No hidden costs**: Includes bandwidth, storage

## Summary

| Component | Current | Location | Update Process |
|-----------|---------|----------|----------------|
| Frontend UI | Vercel | https://tcheiner.com | Auto-deploy on git push |
| Chatbot API | AWS Lambda | API Gateway endpoint | Manual: build + terraform |
| FAISS Index | Container | Bundled in Docker image | Manual rebuild + redeploy |
| API Keys | AWS SSM | Parameter Store | Manual update in AWS console |

**Key Insight**: The vectorstore is NOT separate infrastructure - it's baked into your deployment artifact (Docker container). This is actually simpler than having separate storage, but requires explicit rebuild steps when content changes.
