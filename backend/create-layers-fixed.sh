#!/bin/bash

# Fixed Lambda Layer Creation Script for AWS Lambda (arm64)
# This creates properly structured layers with correct Linux arm64 architecture

set -e

echo "🔧 Creating Lambda layers for arm64 Lambda runtime..."

# Clean up old layers
echo "🧹 Cleaning up old layers..."
rm -rf layer-*-fixed/
rm -f *-layer-fixed.zip

# Create layer directories
mkdir -p layer-dependencies-fixed/python
mkdir -p layer-faiss-fixed/python

echo "📦 Installing dependencies using Docker for Linux arm64 compatibility..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Core dependencies layer (FastAPI, Mangum, etc.)
echo "📦 Building core dependencies layer..."
docker run --rm --platform linux/arm64 \
    -v $(pwd)/layer-dependencies-fixed:/output \
    -w /workspace \
    python:3.12-slim bash -c "
    set -e
    apt-get update && apt-get install -y gcc g++ python3-dev
    pip install --upgrade pip
    
    # Core FastAPI stack
    pip install --target /output/python --no-deps \
        fastapi==0.116.1 \
        mangum==0.19.0 \
        pydantic==2.11.7 \
        pydantic-core==2.33.2 \
        python-dotenv==1.1.1 \
        uvicorn==0.23.2 \
        starlette==0.47.3 \
        anyio==4.10.0 \
        sniffio==1.3.1 \
        idna==3.10 \
        typing-extensions==4.15.0 \
        annotated-types==0.7.0
    
    # HTTP and JSON handling
    pip install --target /output/python --no-deps \
        httpx==0.28.1 \
        httpcore==1.0.9 \
        h11==0.16.0 \
        certifi \
        charset-normalizer==3.4.3 \
        urllib3==2.5.0 \
        requests==2.32.5 \
        requests-toolbelt==1.0.0
    
    echo '✅ Core dependencies installed'
"

# AI/ML dependencies layer (LangChain, OpenAI, etc.)
echo "📦 Building AI/ML dependencies layer..."
docker run --rm --platform linux/arm64 \
    -v $(pwd)/layer-faiss-fixed:/output \
    -w /workspace \
    python:3.12-slim bash -c "
    set -e
    apt-get update && apt-get install -y gcc g++ python3-dev gfortran libopenblas-dev
    pip install --upgrade pip
    
    # LangChain ecosystem
    pip install --target /output/python \
        langchain==0.3.27 \
        langchain-openai==0.3.32 \
        langchain-core==0.3.75 \
        langchain-community==0.3.27 \
        langchain-text-splitters==0.3.11
    
    # OpenAI and tokenization
    pip install --target /output/python \
        openai==1.102.0 \
        tiktoken==0.11.0 \
        regex \
        distro
    
    # FAISS and numpy (compiled for arm64)
    pip install --target /output/python \
        faiss-cpu==1.11.0 \
        'numpy>=1.21.0,<2.0.0'
    
    # Additional utilities
    pip install --target /output/python \
        tenacity==9.1.2 \
        tqdm==4.67.1 \
        packaging==25.0 \
        langsmith==0.4.21
    
    echo '✅ AI/ML dependencies installed'
"

# Copy FAISS vectorstore data
echo "📁 Copying FAISS vectorstore data..."
if [ -d "chatbot/faiss_index" ]; then
    mkdir -p layer-faiss-fixed/python/faiss_index
    cp -r chatbot/faiss_index/* layer-faiss-fixed/python/faiss_index/
    echo "✅ Vectorstore copied to layer from chatbot/faiss_index/"
elif [ -d "faiss_index" ]; then
    mkdir -p layer-faiss-fixed/python/faiss_index
    cp -r faiss_index/* layer-faiss-fixed/python/faiss_index/
    echo "✅ Vectorstore copied to layer from faiss_index/"
else
    echo "⚠️  Warning: No faiss_index found in chatbot/ or current directory"
    echo "    You'll need to rebuild your vectorstore first"
fi

# Create ZIP files
echo "📦 Creating layer ZIP files..."
cd layer-dependencies-fixed
zip -r ../dependencies-layer-fixed.zip python/ -q
cd ../layer-faiss-fixed
zip -r ../faiss-layer-fixed.zip python/ -q
cd ..

# Get file sizes
deps_size=$(du -h dependencies-layer-fixed.zip | cut -f1)
faiss_size=$(du -h faiss-layer-fixed.zip | cut -f1)

echo ""
echo "✅ Layer creation completed successfully!"
echo "📄 Created files:"
echo "   dependencies-layer-fixed.zip (${deps_size})"
echo "   faiss-layer-fixed.zip (${faiss_size})"
echo ""
echo "🚀 Next steps:"
echo "   1. Upload these layers to AWS Lambda"
echo "   2. Update your Terraform configuration"
echo "   3. Deploy your function with the corrected layers"
echo ""
echo "💡 These layers are now compatible with Linux arm64 Lambda runtime!"