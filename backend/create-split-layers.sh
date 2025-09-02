#!/bin/bash

# Create multiple smaller layers to stay under 50MB limit - FIXED VERSION
# This version builds from requirements instead of extracting old layers

set -e
cd /Users/crombie/tcheiner/tcheiner-astro-bento/backend

echo "🔨 Creating split layers under 50MB each (from scratch)..."

# Clean up old split layers
rm -rf layer-*-split/
rm -f *-split.zip

# Create directories for split layers  
mkdir -p layer-core-split/python
mkdir -p layer-ai-split/python  
mkdir -p layer-faiss-split/python
mkdir -p layer-langchain-split/python

echo "📦 Installing dependencies with Docker (arm64)..."

# Install core dependencies (web stack only)
echo "📋 Layer 1: Core web dependencies"
docker run --platform linux/arm64 --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "
pip install --target /app/layer-core-split/python \
fastapi==0.115.12 \
mangum \
pydantic \
starlette \
uvicorn \
anyio \
sniffio \
idna \
typing-extensions \
annotated-types \
h11 \
httpcore \
httpx \
certifi \
charset-normalizer \
urllib3 \
requests \
python-dotenv \
tenacity \
PyYAML \
packaging"

# Install AI core dependencies with jsonpatch and distro
echo "📋 Layer 2: AI core dependencies (LangChain core, OpenAI, jsonpatch, distro)"
docker run --platform linux/arm64 --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "
pip install --target /app/layer-ai-split/python \
langchain-core \
langchain-openai \
openai \
tiktoken \
langsmith \
jsonpatch \
jsonpointer \
distro"

# Install FAISS and computational dependencies (no-deps for langchain to avoid jsonpatch conflict)
echo "📋 Layer 3: FAISS, NumPy and web client dependencies"
docker run --platform linux/arm64 --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "
pip install --target /app/layer-faiss-split/python \
faiss-cpu \
numpy \
orjson \
aiohttp \
multidict \
yarl \
frozenlist \
aiosignal \
attrs \
tqdm \
packaging \
regex"

# Install langchain-text-splitters without dependencies to avoid jsonpatch conflict
docker run --platform linux/arm64 --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "
pip install --target /app/layer-faiss-split/python --no-deps \
langchain-text-splitters"

# Install LangChain community packages (separate layer) - minimal install
echo "📋 Layer 4: LangChain community packages (minimal)"  
docker run --platform linux/arm64 --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "
pip install --target /app/layer-langchain-split/python \
--no-deps \
langchain \
langchain-community"

# Copy FAISS index data
echo "📋 Copying FAISS vectorstore data..."
if [ -d "chatbot/faiss_index" ]; then
    cp -r chatbot/faiss_index layer-faiss-split/python/
    echo "✅ FAISS index copied"
else
    echo "⚠️ No FAISS index found at chatbot/faiss_index"
fi

echo "📦 Creating ZIP files..."
cd layer-core-split && zip -r ../core-dependencies-split.zip python/ -q
cd ../layer-ai-split && zip -r ../ai-dependencies-split.zip python/ -q  
cd ../layer-faiss-split && zip -r ../faiss-vectorstore-split.zip python/ -q
cd ../layer-langchain-split && zip -r ../langchain-community-split.zip python/ -q
cd ..

# Clean up
rm -rf layer-*-split/

# Check sizes and enforce limits
echo "📏 Layer sizes:"
ls -lah *-split.zip | awk '{print $5, $9}'

echo ""
echo "🔍 Checking AWS Lambda layer size limits..."

# Check each layer size (50MB compressed limit)
LIMIT_MB=50
LIMIT_BYTES=$((LIMIT_MB * 1024 * 1024))

for zip_file in *-split.zip; do
    size_bytes=$(stat -f%z "$zip_file" 2>/dev/null || stat -c%s "$zip_file" 2>/dev/null)
    size_mb=$((size_bytes / 1024 / 1024))
    
    if [ $size_bytes -gt $LIMIT_BYTES ]; then
        echo "❌ ERROR: $zip_file is ${size_mb}MB (over ${LIMIT_MB}MB limit)"
        echo "   This layer will be rejected by AWS Lambda!"
        exit 1
    else
        echo "✅ $zip_file: ${size_mb}MB (under ${LIMIT_MB}MB limit)"
    fi
done

echo ""
echo "✅ All layers are under AWS Lambda size limits!"
echo ""
echo "Split layers created:"
echo "   core-dependencies-split.zip (FastAPI, web stack, common utils)"  
echo "   ai-dependencies-split.zip (LangChain core, OpenAI)"
echo "   faiss-vectorstore-split.zip (FAISS, NumPy, vectorstore, aiohttp)"
echo "   langchain-community-split.zip (LangChain community packages, no-deps)"