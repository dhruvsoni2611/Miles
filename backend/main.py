from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Miles API",
    description="AI-powered backend with LangGraph",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic health check endpoint
@app.get("/")
async def root():
    return {"message": "Miles API is running!"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Example LangGraph endpoint (to be expanded)
@app.post("/api/langgraph/workflow")
async def run_workflow(data: dict):
    # Placeholder for LangGraph workflow
    return {"result": "Workflow executed", "data": data}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
