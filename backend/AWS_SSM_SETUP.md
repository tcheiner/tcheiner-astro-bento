# AWS SSM Parameter Store Setup Guide

This guide shows how to securely manage secrets using AWS SSM Parameter Store for both local development and production.

## 🔐 **Current Security Setup**

The application now automatically:
1. **Tries environment variable first** (for local development convenience)
2. **Falls back to AWS SSM Parameter Store** (for production security)

## 🚀 **Quick Setup for Local Development**

### Option 1: Use Environment Variable (Simplest)
```bash
cd backend
echo "OPENAI_API_KEY=your-new-key-here" >> .env
```

### Option 2: Use AWS SSM (Most Secure)
```bash
# 1. Configure AWS CLI
aws configure --profile tcheiner
# Enter: Access Key ID, Secret Access Key, us-east-1, json

# 2. Set profile for session
export AWS_PROFILE=tcheiner

# 3. Test SSM access
aws ssm get-parameter --name "/myapp/OPENAI_API_KEY" --with-decryption

# 4. Start your app (will automatically use SSM)
uvicorn chatbot.main:app --reload
```

## 🔧 **Detailed AWS Setup**

### 1. **Create IAM User for Local Development**
```bash
# Create IAM user
aws iam create-user --user-name chatbot-dev

# Create access key
aws iam create-access-key --user-name chatbot-dev
# Save the Access Key ID and Secret Access Key
```

### 2. **Create IAM Policy for SSM Access**
```bash
# Create policy file
cat > ssm-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:GetParameters",
                "ssm:PutParameter"
            ],
            "Resource": "arn:aws:ssm:us-east-1:149536489028:parameter/myapp/*"
        }
    ]
}
EOF

# Create and attach policy
aws iam create-policy --policy-name ChatbotSSMAccess --policy-document file://ssm-policy.json
aws iam attach-user-policy --user-name chatbot-dev --policy-arn arn:aws:iam::149536489028:policy/ChatbotSSMAccess
```

### 3. **Configure AWS CLI Profile**
```bash
# Configure profile with the access key from step 1
aws configure --profile chatbot-dev
# Access Key ID: [from step 1]
# Secret Access Key: [from step 1] 
# Default region: us-east-1
# Default output format: json

# Set as default profile
export AWS_PROFILE=chatbot-dev
echo 'export AWS_PROFILE=chatbot-dev' >> ~/.bashrc  # or ~/.zshrc
```

### 4. **Manage Parameters**
```bash
# Set your OpenAI API key (do this after revoking the old one!)
aws ssm put-parameter --name "/myapp/OPENAI_API_KEY" --value "your-new-openai-key" --type "SecureString" --overwrite

# List all parameters
aws ssm get-parameters-by-path --path "/myapp" --recursive

# Get parameter value
aws ssm get-parameter --name "/myapp/OPENAI_API_KEY" --with-decryption

# Delete parameter (if needed)
aws ssm delete-parameter --name "/myapp/OPENAI_API_KEY"
```

## 🔄 **Development Workflows**

### Local Development with Environment Variable
```bash
cd backend
source ../.venv/bin/activate

# Use .env file (convenient but less secure)
echo "OPENAI_API_KEY=sk-your-local-key" >> .env

uvicorn chatbot.main:app --reload
```

### Local Development with AWS SSM (Recommended)
```bash
cd backend
source ../.venv/bin/activate

# Ensure AWS_PROFILE is set
export AWS_PROFILE=chatbot-dev

# No .env file needed - will use SSM automatically
uvicorn chatbot.main:app --reload
```

### Production (AWS Lambda)
```bash
# Production automatically uses SSM Parameter Store
# No additional configuration needed
./build-container.sh
```

## 🛠️ **Troubleshooting**

### "Failed to retrieve API key from SSM"
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check parameter exists
aws ssm get-parameter --name "/myapp/OPENAI_API_KEY" --with-decryption

# Check permissions
aws iam list-attached-user-policies --user-name chatbot-dev
```

### "NoCredentialsError"
```bash
# Set AWS profile
export AWS_PROFILE=chatbot-dev

# Or configure default credentials
aws configure
```

### "Access Denied"
```bash
# Verify IAM policy is attached
aws iam get-user-policy --user-name chatbot-dev --policy-name ChatbotSSMAccess

# Check policy document
aws iam get-policy --policy-arn arn:aws:iam::149536489028:policy/ChatbotSSMAccess
```

## 🔐 **Security Best Practices**

✅ **DO:**
- Use AWS SSM Parameter Store for production secrets
- Use IAM users with minimal required permissions
- Rotate API keys regularly
- Use SecureString type for sensitive parameters

❌ **DON'T:**
- Commit secrets to Git
- Use overly broad IAM permissions
- Share AWS access keys
- Store secrets in plain text files

## 🏗️ **Code Implementation**

The backend automatically handles both approaches:

```python
def get_openai_api_key():
    # Try environment variable first (local development)
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return api_key
    
    # Fallback to AWS SSM Parameter Store
    try:
        import boto3
        ssm = boto3.client('ssm')
        response = ssm.get_parameter(
            Name='/myapp/OPENAI_API_KEY',
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except Exception as e:
        raise ValueError("OPENAI_API_KEY not found")
```

This approach provides:
- **Flexibility**: Environment variables for quick local development
- **Security**: AWS SSM for production and secure local development
- **Automatic fallback**: Works in both environments without code changes