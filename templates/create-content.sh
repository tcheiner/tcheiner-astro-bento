#!/bin/bash

# Script to create new content files from templates
# Usage: ./create-content.sh <type> [filename]
# Example: ./create-content.sh post "my-new-post"

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    echo "Usage: $0 <type> [filename]"
    echo "Types: experience, post, project, book, recipe"
    echo "Example: $0 post 'my-new-post'"
    exit 1
fi

TYPE=$1
FILENAME=${2:-""}
TEMPLATE_FILE="templates/${TYPE}-template.mdx"
CONTENT_DIR="src/content/${TYPE}s"

# Handle plural forms
case $TYPE in
    "experience")
        CONTENT_DIR="src/content/experiences"
        ;;
    "post")
        CONTENT_DIR="src/content/posts"
        ;;
    "project")
        CONTENT_DIR="src/content/projects"
        ;;
    "book")
        CONTENT_DIR="src/content/books"
        ;;
    "recipe")
        CONTENT_DIR="src/content/recipes"
        ;;
    *)
        echo "Unknown type: $TYPE"
        echo "Valid types: experience, post, project, book, recipe"
        exit 1
        ;;
esac

# Check if template exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "Template not found: $TEMPLATE_FILE"
    exit 1
fi

# Create target file with proper naming convention
TODAY=$(date +%Y-%m-%d)
if [ -n "$FILENAME" ]; then
    # Use provided filename
    TARGET_FILE="${CONTENT_DIR}/${FILENAME}.mdx"
else
    # Use default date-based naming
    TARGET_FILE="${CONTENT_DIR}/${TYPE}-${TODAY}.mdx"
fi

if [ -f "$TARGET_FILE" ]; then
    echo "File already exists: $TARGET_FILE"
    echo "Do you want to overwrite? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
fi

# Copy template to target location and replace date placeholders
cp "$TEMPLATE_FILE" "$TARGET_FILE"

# Replace date placeholders with today's date
sed -i '' "s/2025-01-01/$TODAY/g" "$TARGET_FILE"

echo "✅ Created: $TARGET_FILE"
echo "📝 Edit the file to add your content"
echo "🔍 Validate with: node validate-mdx.js"
