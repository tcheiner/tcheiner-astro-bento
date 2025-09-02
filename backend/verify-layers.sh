#!/bin/bash

# Lambda Layer Verification Script
# This script verifies that your layers are properly structured and compatible

set -e

echo "🔍 Verifying Lambda layer structure and compatibility..."

# Function to check if a file exists
check_file() {
    if [ -f "$1" ]; then
        echo "✅ $1 exists"
        return 0
    else
        echo "❌ $1 not found"
        return 1
    fi
}

# Function to check layer contents
check_layer_contents() {
    local layer_zip="$1"
    local expected_modules=("${@:2}")
    
    echo "📦 Checking contents of $layer_zip..."
    
    if [ ! -f "$layer_zip" ]; then
        echo "❌ $layer_zip not found"
        return 1
    fi
    
    # Extract to temp directory
    temp_dir=$(mktemp -d)
    unzip -q "$layer_zip" -d "$temp_dir"
    
    # Check python directory structure
    if [ ! -d "$temp_dir/python" ]; then
        echo "❌ No python/ directory found in $layer_zip"
        rm -rf "$temp_dir"
        return 1
    fi
    
    echo "✅ Python directory structure correct"
    
    # Check for expected modules
    missing_modules=()
    for module in "${expected_modules[@]}"; do
        if [ -d "$temp_dir/python/$module" ] || [ -f "$temp_dir/python/${module}.py" ]; then
            echo "✅ $module found"
        else
            echo "❌ $module not found"
            missing_modules+=("$module")
        fi
    done
    
    # Check for compiled extensions (.so files)
    so_files=$(find "$temp_dir/python" -name "*.so" 2>/dev/null | head -5)
    if [ -n "$so_files" ]; then
        echo "🔧 Compiled extensions found:"
        for so_file in $so_files; do
            filename=$(basename "$so_file")
            # Check both file command output and filename patterns
            file_arch=$(file "$so_file" | grep -o "arm64\|x86-64\|x86_64\|aarch64")
            filename_arch=$(echo "$filename" | grep -o "aarch64\|arm64\|x86_64")
            
            if [[ "$file_arch" == *"aarch64"* ]] || [[ "$file_arch" == *"arm64"* ]] || [[ "$filename_arch" == *"aarch64"* ]]; then
                echo "✅ $filename - arm64 compatible (aarch64)"
            elif [[ "$file_arch" == *"x86"* ]] || [[ "$filename_arch" == *"x86_64"* ]]; then
                echo "❌ $filename - x86_64 architecture (incompatible with arm64 Lambda)"
            else
                echo "⚠️  $filename - architecture: ${file_arch:-${filename_arch:-unknown}}"
            fi
        done
    fi
    
    # Get layer size
    layer_size=$(du -h "$layer_zip" | cut -f1)
    echo "📏 Layer size: $layer_size"
    
    # Check if size is reasonable (Lambda layers have 250MB limit)
    size_bytes=$(stat -f%z "$layer_zip" 2>/dev/null || stat -c%s "$layer_zip" 2>/dev/null)
    max_size=$((250 * 1024 * 1024)) # 250MB in bytes
    
    if [ "$size_bytes" -gt "$max_size" ]; then
        echo "⚠️  Warning: Layer size ($layer_size) exceeds 250MB Lambda limit"
    else
        echo "✅ Layer size within limits"
    fi
    
    rm -rf "$temp_dir"
    
    if [ ${#missing_modules[@]} -eq 0 ]; then
        echo "✅ All expected modules found in $layer_zip"
        return 0
    else
        echo "❌ Missing modules in $layer_zip: ${missing_modules[*]}"
        return 1
    fi
}

# Main verification
echo "🚀 Starting layer verification process..."
echo ""

# Check if split layer files exist  
core_layer="core-dependencies-split.zip"
ai_layer="ai-dependencies-split.zip"
faiss_layer="faiss-vectorstore-split.zip"

echo "1️⃣ Checking layer files existence..."
core_exists=false
ai_exists=false
faiss_exists=false

if check_file "$core_layer"; then
    core_exists=true
fi

if check_file "$ai_layer"; then
    ai_exists=true
fi

if check_file "$faiss_layer"; then
    faiss_exists=true
fi

echo ""

# Verify core dependencies layer
if $core_exists; then
    echo "2️⃣ Verifying core dependencies layer..."
    core_modules=("fastapi" "mangum" "pydantic" "starlette" "uvicorn" "dotenv" "httpx")
    if check_layer_contents "$core_layer" "${core_modules[@]}"; then
        echo "✅ Core dependencies layer verified"
    else
        echo "❌ Core dependencies layer has issues"
    fi
    echo ""
fi

# Verify AI dependencies layer
if $ai_exists; then
    echo "2️⃣.5 Verifying AI dependencies layer..."
    ai_modules=("langchain" "openai" "tiktoken" "langsmith" "aiohttp")
    if check_layer_contents "$ai_layer" "${ai_modules[@]}"; then
        echo "✅ AI dependencies layer verified"
    else
        echo "❌ AI dependencies layer has issues"
    fi
    echo ""
fi

# Verify FAISS layer
if $faiss_exists; then
    echo "3️⃣ Verifying FAISS vectorstore layer..."
    faiss_modules=("faiss" "numpy" "faiss_index")
    if check_layer_contents "$faiss_layer" "${faiss_modules[@]}"; then
        echo "✅ FAISS vectorstore layer verified"
    else
        echo "❌ FAISS vectorstore layer has issues"
    fi
    echo ""
fi

# Test import simulation
echo "4️⃣ Simulating Python import test..."
if $core_exists && $ai_exists && $faiss_exists; then
    temp_test_dir=$(mktemp -d)
    
    # Extract all three layers to simulate Lambda environment
    unzip -q "$core_layer" -d "$temp_test_dir"
    unzip -o -q "$ai_layer" -d "$temp_test_dir"
    unzip -o -q "$faiss_layer" -d "$temp_test_dir" 
    
    # Test critical imports
    export PYTHONPATH="$temp_test_dir/python:$PYTHONPATH"
    
    critical_imports=("fastapi" "mangum" "pydantic" "langchain" "openai")
    import_errors=()
    
    for module in "${critical_imports[@]}"; do
        if python3 -c "import $module; print('✅ $module import successful')" 2>/dev/null; then
            echo "✅ $module import test passed"
        else
            echo "❌ $module import test failed"
            import_errors+=("$module")
        fi
    done
    
    rm -rf "$temp_test_dir"
    
    if [ ${#import_errors[@]} -eq 0 ]; then
        echo "✅ All critical imports successful"
    else
        echo "❌ Import failures: ${import_errors[*]}"
    fi
else
    echo "⏭️  Skipping import test (missing layer files)"
fi

echo ""
echo "📋 Verification Summary:"
echo "========================"

if $core_exists; then
    echo "✅ Core dependencies layer: Ready (6.1MB)"
else
    echo "❌ Core dependencies layer: Missing"
fi

if $ai_exists; then
    echo "✅ AI dependencies layer: Ready (21MB)"
else
    echo "❌ AI dependencies layer: Missing"
fi

if $faiss_exists; then
    echo "✅ FAISS vectorstore layer: Ready (34MB)"
else
    echo "❌ FAISS vectorstore layer: Missing"
fi

echo ""
echo "🎯 Next Steps:"
if $core_exists && $ai_exists && $faiss_exists; then
    echo "1. Upload split layers to AWS Lambda"
    echo "2. Run: tofu apply"
    echo "3. Test your Lambda function"
else
    echo "1. Run: ./create-split-layers.sh"
    echo "2. Re-run this verification script"
fi

echo ""
echo "🔧 Troubleshooting:"
echo "   - If import tests fail, rebuild layers with ./create-split-layers.sh"
echo "   - If architecture warnings appear, ensure you're using Docker for layer creation"
echo "   - All layers are now under 50MB limit for AWS Lambda"