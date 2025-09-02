#!/bin/bash

# Exit on any error
set -e

# Configuration
PYTHON_VERSION="3.12"
LAYER_NAME="chatbot-faiss-vs"
REGION="us-east-1"

# Directories
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LAYER_DIR="${SCRIPT_DIR}/layer"
PYTHON_DIR="${LAYER_DIR}/python/lib/python${PYTHON_VERSION}/site-packages"

# Create clean layer directory
echo "🧹 Cleaning previous layer..."
rm -rf "${LAYER_DIR}"
mkdir -p "${PYTHON_DIR}"

# Create virtual environment
# Activate existing virtual environment
source venv/bin/activate

# Core dependencies
pip install \
    numpy \
    torch==2.2.2 \
    transformers==4.38.2 \
    sentence-transformers==2.6.1 \
    langchain==0.1.14 \
    openai==1.12.0 \
    tiktoken==0.6.0

# Try multiple FAISS installation methods
pip install faiss-cpu==1.7.4 || \
pip install --only-binary=:all: faiss-cpu==1.7.4 || \
pip install annoy
# Diagnostic output
echo "🕵️ Installed packages:"
pip list

# Copy FAISS index
echo "🗂️ Copying FAISS index..."
cp -r "${SCRIPT_DIR}/faiss_index" "${LAYER_DIR}/python/"

# Create layer zip
echo "🗜️ Creating layer zip..."
cd "${LAYER_DIR}"
zip -r "${SCRIPT_DIR}/chatbot-faiss-vs.zip" python

# Create Lambda function zip
echo "🚀 Creating Lambda function zip..."
cd "${SCRIPT_DIR}/chatbot"
zip -r "${SCRIPT_DIR}/chatbot-function.zip" .

# Cleanup
deactivate
rm -rf venv

echo "✅ Zip creation complete!"
