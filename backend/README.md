# TC Heiner Chatbot Backend

AI-powered chatbot using FastAPI + RAG (Retrieval Augmented Generation) to answer questions about TC Heiner's work and projects. Features a freemium model with content filtering and deploys to AWS Lambda via containers.

## Quick Start

### Local Development Setup
1. **Environment Setup**:
   ```bash
   cd backend
   source ../.venv/bin/activate  # venv is in parent directory
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   - Create `.env` file with your OpenAI API key:
   ```bash
   echo "OPENAI_API_KEY=sk-your-key-here" > .env
   echo "ALLOWED_ORIGINS=http://localhost:4321,https://tcheiner.com" >> .env
   ```

3. **Ensure FAISS Index Exists**:
   ```bash
   # Check if index exists
   ls chatbot/faiss_index/
   
   # If missing, rebuild it
   python -c "from chatbot.services import rebuild_vectorstore; rebuild_vectorstore()"
   ```

4. **Start Development Server**:
   ```bash
   uvicorn chatbot.main:app --reload
   ```

5. **Test Locally**:
   - Swagger UI: http://127.0.0.1:8000/docs
   - CLI test:
   ```bash
   curl -X POST "http://127.0.0.1:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "Tell me about TC"}'
   ```

### Deploy to AWS

**Prerequisites**: AWS CLI configured, Docker running, ECR repository exists

1. **Build and Push Container**:
   ```bash
   # Automated (recommended)
   ./build-container.sh
   
   # Manual steps
   docker build --platform linux/arm64 -t chatbot-lambda .
   docker tag chatbot-lambda 149536489028.dkr.ecr.us-east-1.amazonaws.com/chatbot-lambda:latest
   docker push 149536489028.dkr.ecr.us-east-1.amazonaws.com/chatbot-lambda:latest
   ```

2. **Update Lambda Function**:
   ```bash
   aws lambda update-function-code \
     --function-name chatbot-api \
     --image-uri 149536489028.dkr.ecr.us-east-1.amazonaws.com/chatbot-lambda:latest
   ```

3. **Deploy Infrastructure** (if needed):
   ```bash
   cd terraform
   tofu init    # First time only
   tofu apply
   ```

4. **Test Production**:
   ```bash
   curl -X POST "https://5f3ysv93x1.execute-api.us-east-1.amazonaws.com/prod/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "Tell me about TC"}'
   ```

## Content Management & FAISS Index

The FAISS vectorstore indexes content from `../src/content/` for RAG responses.

### When to Rebuild FAISS Index
- ✅ After adding new blog posts, projects, or experiences
- ✅ After editing existing content in `../src/content/`
- ✅ Before deploying to ensure latest content is available
- ✅ If chatbot responses seem outdated or missing recent content

### How to Rebuild FAISS Index

1. **Quick Rebuild** (processes only changed files):
   ```bash
   cd backend
   source ../.venv/bin/activate
   python -c "from chatbot.services import rebuild_vectorstore; rebuild_vectorstore()"
   ```

2. **Full Rebuild** (reprocesses all content):
   ```bash
   cd backend
   source ../.venv/bin/activate
   rm -f chatbot/last_rebuild.json  # Remove timestamp tracking
   python -c "from chatbot.services import rebuild_vectorstore; rebuild_vectorstore()"
   ```

3. **Direct Content Ingestion** (alternative method):
   ```bash
   cd backend
   python chatbot/content_ingest.py
   ```

### Complete Content Update Workflow

When you add/edit content in `../src/content/`:

```bash
# 1. Rebuild FAISS index
cd backend
python -c "from chatbot.services import rebuild_vectorstore; rebuild_vectorstore()"

# 2. Test locally (optional)
uvicorn chatbot.main:app --reload
curl -X POST "http://127.0.0.1:8000/ask" -H "Content-Type: application/json" -d '{"question": "What are your recent projects?"}'

# 3. Deploy to AWS
./build-container.sh
aws lambda update-function-code --function-name chatbot-api --image-uri 149536489028.dkr.ecr.us-east-1.amazonaws.com/chatbot-lambda:latest

# 4. Test production
curl -X POST "https://5f3ysv93x1.execute-api.us-east-1.amazonaws.com/prod/ask" -d '{"question": "What are your recent projects?"}'
```

**What gets indexed:**
- Blog posts: `../src/content/posts/*.mdx`
- Projects: `../src/content/projects/*.mdx` 
- Experiences: `../src/content/experiences/*.mdx`
- Resume and other content: `../src/content/**/*.{md,mdx,pdf}`

**⚠️ Important**: The FAISS index is included in the Docker container, so you **must rebuild and redeploy the container** after updating the vectorstore for changes to take effect in AWS Lambda.

## Architecture

**Key Features:**
- **Freemium Model**: 5 free GPT-4o-mini questions, then user provides API key
- **Content Filtering**: Blocks non-TC related questions to prevent API abuse
- **RAG System**: FAISS vector search + OpenAI embeddings
- **Container Deployment**: 10GB Lambda containers (vs 250MB layer limit)

**Core Files:**
- `main.py`: FastAPI app + Lambda handler
- `services.py`: FAISS vectorstore + QA chain management  
- `models.py`: API request/response schemas
- `content_ingest.py`: Content processing pipeline

## Deployment Workflow

### Complete Deployment Steps

| Step | Command | When Required |
|------|---------|---------------|
| 1. Rebuild FAISS | `python -c "from chatbot.services import rebuild_vectorstore; rebuild_vectorstore()"` | After content changes |
| 2. Build container | `./build-container.sh` | After code/content changes |
| 3. Deploy infrastructure | `cd terraform && tofu apply` | Infrastructure changes |
| 4. Test | `curl -X POST "https://api-url/prod/ask" ...` | Always |

### Container Deployment

Uses **AWS Lambda Container Images** for better ML/AI support:

```bash
# Automated (recommended)
./build-container.sh

# Manual steps
docker build --platform linux/arm64 -t chatbot-lambda .
docker tag chatbot-lambda 149536489028.dkr.ecr.us-east-1.amazonaws.com/chatbot-lambda:latest
docker push 149536489028.dkr.ecr.us-east-1.amazonaws.com/chatbot-lambda:latest
aws lambda update-function-code --function-name chatbot-api --image-uri 149536489028.dkr.ecr.us-east-1.amazonaws.com/chatbot-lambda:latest
```

**Container Benefits:**
- 10GB size limit (vs 250MB layers)
- All dependencies included
- No import/cold start issues
- Standard Docker workflow

## Environment Setup

**Required Environment Variables:**
- `OPENAI_API_KEY`: OpenAI API key (AWS SSM for Lambda)
- `ALLOWED_ORIGINS`: CORS origins (comma-separated)

**Local `.env` example:**
```
OPENAI_API_KEY=sk-...
ALLOWED_ORIGINS=http://localhost:4321,https://tcheiner.com
```

## API Endpoints

- `POST /ask`: Main chatbot endpoint (supports user API keys)
- `OPTIONS /ask`: CORS preflight handling
- `GET /docs`: Swagger documentation

**Request Format:**
```json
{
  "question": "Tell me about TC's experience",
  "userApiKey": "sk-..." // Optional, for paid tier
}
```

## Common Issues

**Missing FAISS Index**: Run `python -c "from chatbot.services import rebuild_vectorstore; rebuild_vectorstore()"`

**Container Build Fails**: Ensure Docker running, AWS credentials configured

**CORS Errors**: Check `ALLOWED_ORIGINS` in environment variables

**API Key Errors**: Verify OpenAI API key in `.env` (local) or AWS SSM (Lambda)

## Development Tips

1. **Content Changes**: Always rebuild FAISS before deploying
2. **Local Testing**: Use Swagger docs at `/docs` for interactive testing  
3. **Container Updates**: Use `./build-container.sh` for automated deployment
4. **Infrastructure**: Use `tofu apply` for AWS resource changes

## Architecture Notes

- **Freemium Model**: First 5 questions use system API key, then requires user key
- **Content Filtering**: Regex patterns block abuse while allowing TC-related queries
- **Vector Search**: FAISS similarity search with k=5, threshold=0.5
- **Caching**: Global vectorstore/QA chain caching reduces cold starts