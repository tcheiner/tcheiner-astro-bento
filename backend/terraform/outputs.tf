# Output value definitions

output "function_name" {
  description = "Name of the Lambda function."

  value = aws_lambda_function.chatbot_lambda.function_name
}



output "base_url" {
  description = "Base URL for API Gateway stage."

  value = "https://${aws_api_gateway_rest_api.chatbot_rest_api.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_api_gateway_stage.prod_stage.stage_name}"

}
