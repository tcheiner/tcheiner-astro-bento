# Data sources
data "aws_ssm_parameter" "openai_api_key" {
  name = "/myapp/OPENAI_API_KEY"
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_chatbot_role" {
  name = "serverless_lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Sid    = ""
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# IAM Policy for SSM access
resource "aws_iam_role_policy" "lambda_ssm_policy" {
  name = "lambda_ssm_access"
  role = aws_iam_role.lambda_chatbot_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = data.aws_ssm_parameter.openai_api_key.arn
      }
    ]
  })
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_chatbot_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda Function using Container Image
resource "aws_lambda_function" "chatbot_lambda" {
  function_name = "chatbot-api"
  package_type  = "Image"
  image_uri     = "149536489028.dkr.ecr.us-east-1.amazonaws.com/chatbot-lambda:latest"
  
  role = aws_iam_role.lambda_chatbot_role.arn

  architectures = ["arm64"]
  timeout      = 900
  memory_size  = 512

  # Force update when chatbot code changes - hash key source files
  source_code_hash = base64sha256(join("", [
    fileexists("../chatbot/main.py") ? file("../chatbot/main.py") : "",
    fileexists("../chatbot/sources.py") ? file("../chatbot/sources.py") : "",
    fileexists("../chatbot/confidence.py") ? file("../chatbot/confidence.py") : "",
    fileexists("../chatbot/filters.py") ? file("../chatbot/filters.py") : "",
    fileexists("../requirements.txt") ? file("../requirements.txt") : ""
  ]))

  environment {
    variables = {
      OPENAI_API_KEY = data.aws_ssm_parameter.openai_api_key.value
    }
  }

  depends_on = [
    aws_iam_role.lambda_chatbot_role
  ]

  tags = {
    Environment = "Production"
    Application = "Chatbot"
    Owner       = "TCHeiner"
  }
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_chatbot" {
  name              = "/aws/lambda/${aws_lambda_function.chatbot_lambda.function_name}"
  retention_in_days = 30
}

# REST API Gateway
resource "aws_api_gateway_rest_api" "chatbot_rest_api" {
  name        = "chatbot-rest-api"
  description = "REST API for Chatbot Lambda function"
  tags = {
    Environment = "Production"
    Application = "Chatbot"
    Owner       = "TCHeiner"
  }
}

# Resource (/ask)
resource "aws_api_gateway_resource" "ask_resource" {
  rest_api_id = aws_api_gateway_rest_api.chatbot_rest_api.id
  parent_id   = aws_api_gateway_rest_api.chatbot_rest_api.root_resource_id
  path_part   = "ask"
}

# Method (POST)
resource "aws_api_gateway_method" "post_method" {
  rest_api_id   = aws_api_gateway_rest_api.chatbot_rest_api.id
  resource_id   = aws_api_gateway_resource.ask_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

# Method (OPTIONS) for CORS preflight
resource "aws_api_gateway_method" "options_method" {
  rest_api_id   = aws_api_gateway_rest_api.chatbot_rest_api.id
  resource_id   = aws_api_gateway_resource.ask_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# Lambda Integration
resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.chatbot_rest_api.id
  resource_id             = aws_api_gateway_resource.ask_resource.id
  http_method             = aws_api_gateway_method.post_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.chatbot_lambda.invoke_arn
}

# OPTIONS Integration for CORS preflight
resource "aws_api_gateway_integration" "options_integration" {
  rest_api_id = aws_api_gateway_rest_api.chatbot_rest_api.id
  resource_id = aws_api_gateway_resource.ask_resource.id
  http_method = aws_api_gateway_method.options_method.http_method
  type        = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

# Method Response
resource "aws_api_gateway_method_response" "post_method_response" {
  rest_api_id = aws_api_gateway_rest_api.chatbot_rest_api.id
  resource_id = aws_api_gateway_resource.ask_resource.id
  http_method = aws_api_gateway_method.post_method.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# OPTIONS Method Response for CORS preflight
resource "aws_api_gateway_method_response" "options_method_response" {
  rest_api_id = aws_api_gateway_rest_api.chatbot_rest_api.id
  resource_id = aws_api_gateway_resource.ask_resource.id
  http_method = aws_api_gateway_method.options_method.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Headers" = true
  }
}

# Integration Response  
resource "aws_api_gateway_integration_response" "lambda_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.chatbot_rest_api.id
  resource_id = aws_api_gateway_resource.ask_resource.id
  http_method = aws_api_gateway_method.post_method.http_method
  status_code = aws_api_gateway_method_response.post_method_response.status_code
  
  depends_on = [aws_api_gateway_integration.lambda_integration]
}

# OPTIONS Integration Response for CORS preflight
resource "aws_api_gateway_integration_response" "options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.chatbot_rest_api.id
  resource_id = aws_api_gateway_resource.ask_resource.id
  http_method = aws_api_gateway_method.options_method.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS,POST'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
  }
  
  depends_on = [aws_api_gateway_integration.options_integration]
}

# Deployment
resource "aws_api_gateway_deployment" "chatbot_deployment" {
  rest_api_id = aws_api_gateway_rest_api.chatbot_rest_api.id
  depends_on  = [
    aws_api_gateway_integration.lambda_integration,
    aws_api_gateway_method_response.post_method_response,
    aws_api_gateway_integration_response.lambda_integration_response,
    aws_api_gateway_integration.options_integration,
    aws_api_gateway_method_response.options_method_response,
    aws_api_gateway_integration_response.options_integration_response
  ]
  
  # Force redeployment when configuration changes
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.ask_resource.id,
      aws_api_gateway_method.post_method.id,
      aws_api_gateway_integration.lambda_integration.id,
      aws_api_gateway_method.options_method.id,
      aws_api_gateway_integration.options_integration.id,
    ]))
  }
  
  lifecycle {
    create_before_destroy = true
  }
}

# API Gateway Stage
resource "aws_api_gateway_stage" "prod_stage" {
  deployment_id = aws_api_gateway_deployment.chatbot_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.chatbot_rest_api.id
  stage_name    = "prod"
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "chatbot_api_gw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.chatbot_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.chatbot_rest_api.execution_arn}/*/*"
}

# CloudWatch Log Group for REST API
resource "aws_cloudwatch_log_group" "rest_api_logs" {
  name              = "/aws/apigateway/${aws_api_gateway_rest_api.chatbot_rest_api.name}"
  retention_in_days = 30
  tags = {
    Environment = "Production"
    Application = "Chatbot"
    Owner       = "TCHeiner"
  }
}

# AWS Provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      hashicorp-learn = "lambda-api-gateway"
    }
  }
}
