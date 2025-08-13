"""
FastAPI backend for LexiGraph
Provides REST API for text-to-graph processing
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import asyncio
from pathlib import Path

from core.pipeline import pipeline, get_llm_instance
from core.utils import compile_dot_to_png, generate_unique_filename

def process_lecture(text: str, provider: str, model: str, api_key: str):
    """
    Wrapper function for the core pipeline that matches the FastAPI interface
    
    Args:
        text (str): Input text to process
        provider (str): AI provider to use
        model (str): Model name to use
        api_key (str): API key for the provider
        
    Returns:
        dict: Result with success status, graph_path, and error info
    """
    try:
        # Validate API key
        if not api_key or not api_key.strip():
            return {
                "success": False,
                "error": f"API key is required for {provider}"
            }
        
        # Validate API key format based on provider
        validation_patterns = {
            "anthropic": "sk-ant-",
            "openai": "sk-",
            "openrouter": "sk-or-"
        }
        
        if provider.lower() in validation_patterns:
            expected_pattern = validation_patterns[provider.lower()]
            if not api_key.startswith(expected_pattern):
                return {
                    "success": False,
                    "error": f"Invalid {provider} API key format. {provider} API keys should start with '{expected_pattern}'"
                }
        
        # Set environment variables for provider selection
        os.environ['PROVIDER'] = provider.lower()
        os.environ['MODEL_NAME'] = model
        
        # Set the appropriate API key environment variable
        if provider.lower() == "anthropic":
            os.environ['ANTHROPIC_API_KEY'] = api_key
        elif provider.lower() == "openai":
            os.environ['OPENAI_API_KEY'] = api_key
        elif provider.lower() == "openrouter":
            os.environ['OPENROUTER_API_KEY'] = api_key
        else:
            return {
                "success": False,
                "error": f"Unsupported provider: {provider}"
            }
        
        # Call the core pipeline
        summary, dot_code = pipeline(text)
        
        if dot_code and "digraph" in dot_code:
            # Generate unique filename and compile to PNG
            filename = generate_unique_filename()
            
            # Ensure output directory exists
            output_dir = Path("../output")
            output_dir.mkdir(exist_ok=True)
            print(f"Output directory: {output_dir.absolute()}")
            
            result_path = compile_dot_to_png(dot_code, filename, str(output_dir))
            
            if result_path:
                graph_path = f"{filename}.png"
                print(f"Generated graph: {graph_path}")
                return {
                    "success": True,
                    "graph_path": graph_path,
                    "summary": summary
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to compile DOT code to PNG"
                }
        else:
            return {
                "success": False,
                "error": "Failed to generate valid DOT code from text"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

app = FastAPI(
    title="LexiGraph API",
    description="Transform lecture text into interactive concept graphs",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextInput(BaseModel):
    text: str
    provider: str = "anthropic"
    model: str = "claude-3-5-haiku-20241022"
    api_key: str

class ProcessResponse(BaseModel):
    success: bool
    message: str
    graph_path: Optional[str] = None
    summary: Optional[str] = None
    error: Optional[str] = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "LexiGraph API is running"}

@app.get("/providers")
async def get_providers():
    """Get available AI providers"""
    return {
        "providers": [
            {"id": "openrouter", "name": "OpenRouter"},
            {"id": "anthropic", "name": "Anthropic"},
            {"id": "openai", "name": "OpenAI"}
        ]
    }

@app.get("/models/{provider}")
async def get_models(provider: str):
    """Get available models for a specific provider"""
    models = {
        "anthropic": [
            {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku"},
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet"},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus"}
        ],
        "openai": [
            {"id": "gpt-4o", "name": "GPT-4o"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"}
        ],
        "openrouter": [
            {"id": "anthropic/claude-3.5-haiku", "name": "Claude 3.5 Haiku (OpenRouter)"},
            {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet (OpenRouter)"},
            {"id": "openai/gpt-4o", "name": "GPT-4o (OpenRouter)"},
            {"id": "google/gemini-pro-1.5", "name": "Gemini Pro 1.5 (OpenRouter)"}
        ]
    }
    
    if provider.lower() not in models:
        raise HTTPException(status_code=404, detail=f"Provider {provider} not found")
    
    return {"models": models[provider.lower()]}

@app.post("/process/text", response_model=ProcessResponse)
async def process_text(input_data: TextInput):
    """Process text input and generate concept graph"""
    try:
        # Run the pipeline in a separate thread to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            process_lecture, 
            input_data.text, 
            input_data.provider,
            input_data.model,
            input_data.api_key
        )
        
        if result["success"]:
            return ProcessResponse(
                success=True,
                message="Graph generated successfully",
                graph_path=result.get("graph_path"),
                summary=result.get("summary")
            )
        else:
            return ProcessResponse(
                success=False,
                message="Failed to generate graph",
                error=result.get("error")
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/image/{filename}")
async def serve_image(filename: str):
    """Serve image file for display in the frontend"""
    try:
        # Look for the file in the output directory
        output_dir = Path("../output")
        file_path = output_dir / filename
        
        print(f"Looking for image file: {file_path}")
        print(f"File exists: {file_path.exists()}")
        
        if not file_path.exists():
            # List available files for debugging
            if output_dir.exists():
                files = list(output_dir.glob("*.png"))
                print(f"Available files: {files}")
            else:
                print(f"Output directory {output_dir} does not exist")
            raise HTTPException(status_code=404, detail="Image file not found")
        
        return FileResponse(
            path=str(file_path),
            media_type='image/png'
        )
        
    except Exception as e:
        print(f"Error serving image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_graph(filename: str):
    """Download generated graph file"""
    try:
        # Look for the file in the output directory
        output_dir = Path("../output")
        file_path = output_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='image/png',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
