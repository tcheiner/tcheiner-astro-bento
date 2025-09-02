variable "aws_region" {
  description = "The AWS region to use"
  default     = "us-east-1" # Set a default region or leave it empty
}

variable "aws_account_id" {
  description = "AWS ACCOUNT ID"
  type        = string
  default     = "123456789012"
}

variable "aws_lambda_function_name" {
  type    = string
  default = "chatbot-function"
}

variable "runtime" {
  type    = string
  default = "python3.12"
}


