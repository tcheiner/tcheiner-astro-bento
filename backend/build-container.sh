#!/bin/bash

# Build and push Lambda container to ECR
set -e

# Configuration
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="149536489028"
ECR_REPOSITORY="chatbot-lambda"
IMAGE_TAG="latest"

echo "🐳 Building Lambda container image..."

# Check if ECR repository exists (skip creation if permission denied)
if aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION >/dev/null 2>&1; then
    echo "✅ ECR repository $ECR_REPOSITORY exists"
else
    echo "📦 Creating ECR repository: $ECR_REPOSITORY"
    if ! aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION 2>/dev/null; then
        echo "❌ Failed to create repository. It may already exist or you need ECR permissions."
        echo "💡 Try using an admin AWS profile or ask admin to create: $ECR_REPOSITORY"
        echo "⚠️  Continuing anyway - repository might already exist..."
    fi
fi

# Get ECR login token
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build the image
echo "🔨 Building Docker image..."
docker build -t $ECR_REPOSITORY:$IMAGE_TAG .

# Tag for ECR
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG"
docker tag $ECR_REPOSITORY:$IMAGE_TAG $ECR_URI

# Push to ECR
echo "📤 Pushing image to ECR..."
docker push $ECR_URI

echo "✅ Container image pushed successfully!"
echo "📋 ECR URI: $ECR_URI"
echo ""
echo "🚀 Next steps:"
echo "1. Update terraform/main.tf to use container image"
echo "2. Run 'tofu apply' to deploy"
echo "3. Remove old layer configurations"
