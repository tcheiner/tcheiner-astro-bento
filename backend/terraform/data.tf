data "archive_file" "lambda_chatbot" {
  type        = "zip"
  source_dir  = "${path.module}/../chatbot"
  output_path = "${path.module}/../chatbot-function.zip"
}
