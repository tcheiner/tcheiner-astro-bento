FROM public.ecr.aws/lambda/python:3.12

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements and install dependencies
COPY requirements-clean.txt requirements.txt
RUN pip install -r requirements.txt

# Copy application code
COPY chatbot/ ./chatbot/

# Copy FAISS index data to match expected path
COPY chatbot/faiss_index/ ./chatbot/faiss_index/

# Set the handler (main.py is now in chatbot directory)
CMD ["chatbot.main.handler"]
