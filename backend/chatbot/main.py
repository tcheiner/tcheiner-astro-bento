import os
from logger import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from chatbot.routes import router

load_dotenv()
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
openai_key = os.getenv("OPENAI_API_KEY")
# Create FastAPI app
app = FastAPI(title="Chatbot Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Allow all origins (not recommended for production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include API routes
app.include_router(router)

# Log a message when the app starts
@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI application is starting up...")

# Log a message when the app shuts down
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("FastAPI application is shutting down...")

