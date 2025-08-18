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
                "error": f"API key is required for {provider}. Please enter your {provider} API key."
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
                "error": f"Provider '{provider}' is not supported. Please select Anthropic, OpenAI, or OpenRouter."
            }
        
        # Call the core pipeline
        print(f"🚀 Starting pipeline with provider: {provider}, model: {model}")
        summary, dot_code = pipeline(text)
        
        if dot_code and "digraph" in dot_code:
            print("✅ Pipeline generated valid DOT code")
            # Generate unique filename and compile to PNG
            filename = generate_unique_filename()
            print(f"📝 Generated filename: {filename}")
            
            # Ensure output directory exists
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            print(f"📁 Output directory: {output_dir.absolute()}")
            
            print("🔧 Starting DOT to PNG compilation...")
            result_path = compile_dot_to_png(dot_code, filename, str(output_dir))
            
            if result_path:
                graph_path = f"{filename}.png"
                print(f"✅ Graph generation successful: {graph_path}")
                return {
                    "success": True,
                    "graph_path": graph_path,
                    "summary": summary
                }
            else:
                error_msg = "Failed to generate the graph image. The AI model may have produced invalid graph code. Please try again with different content or a different model."
                print(f"❌ Failed to compile DOT code to PNG - check console for detailed error messages")
                return {
                    "success": False,
                    "error": error_msg
                }
        else:
            error_msg = f"Unable to generate a valid knowledge graph from the provided content. Please try with different text or select a different AI model."
            print(f"❌ Pipeline failed to generate valid DOT code. Generated content: {str(dot_code)[:200]}...")
            return {
                "success": False,
                "error": error_msg
            }
            
    except Exception as e:
        # Log detailed error for debugging
        detailed_error = f"❌ Pipeline execution failed: {str(e)}"
        print(detailed_error)
        
        # Print detailed exception information for debugging
        import traceback
        print(f"🔍 Full error traceback:")
        traceback.print_exc()
        
        # Provide user-friendly error message
        user_friendly_error = "An unexpected error occurred while processing your content. Please try again with different text or select a different AI model."
        
        # Handle specific common errors with better messages
        error_str = str(e).lower()
        if "rate limit" in error_str or "quota" in error_str:
            user_friendly_error = "API rate limit reached. Please wait a moment and try again."
        elif "api key" in error_str or "authentication" in error_str:
            user_friendly_error = "Authentication failed. Please check your API key and try again."
        elif "model" in error_str and "not found" in error_str:
            user_friendly_error = "The selected AI model is not available. Please try a different model."
        elif "timeout" in error_str:
            user_friendly_error = "The request timed out. Please try again with shorter content."
        elif "max_tokens" in error_str:
            user_friendly_error = "The content is too long for the selected model. Please try shorter content or a different model."
        
        return {
            "success": False,
            "error": user_friendly_error
        }

app = FastAPI(
    title="LexiGraph API",
    description="Transform lecture text into interactive concept graphs",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "http://127.0.0.1:3000",  # Local development alt
        "*"  # Allow all origins for now - you can restrict this later
    ],
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
            {"id": "claude-opus-4-1-20250805", "name": "Claude Opus 4.1"},
            {"id": "claude-opus-4-20250514", "name": "Claude Opus 4"},
            {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4"},
            {"id": "claude-3-7-sonnet-20250219", "name": "Claude Sonnet 3.7"},
            {"id": "claude-3-5-haiku-20241022", "name": "Claude Haiku 3.5"}
        ],
        "openai": [
            {"id": "gpt-5", "name": "GPT-5"},
            {"id": "gpt-4.1", "name": "GPT-4.1"},
            {"id": "gpt-4o", "name": "GPT-4o"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"}
        ],
        "openrouter": [
            # Free models
            {"id": "deepseek/deepseek-chat-v3-0324:free", "name": "DeepSeek Chat v3 (Free)"},
            {"id": "deepseek/deepseek-r1-0528:free", "name": "DeepSeek R1 0528 (Free)"},
            {"id": "qwen/qwen3-coder:free", "name": "Qwen 3 Coder (Free)"},
            {"id": "deepseek/deepseek-r1:free", "name": "DeepSeek R1 (Free)"},
            {"id": "moonshotai/kimi-k2:free", "name": "Kimi K2 (Free)"},
            {"id": "qwen/qwen3-235b-a22b:free", "name": "Qwen 3 235B (Free)"},
            {"id": "meta-llama/llama-3.3-70b-instruct:free", "name": "Llama 3.3 70B Instruct (Free)"},
            {"id": "google/gemma-3n-e4b-it:free", "name": "Gemma 3N E4B IT (Free)"},
            {"id": "mistralai/mistral-small-3.1-24b-instruct:free", "name": "Mistral Small 3.1 24B (Free)"},
            {"id": "openai/gpt-oss-20b:free", "name": "GPT OSS 20B (Free)"},
            {"id": "google/gemma-3n-e2b-it:free", "name": "Gemma 3N E2B IT (Free)"},
            {"id": "meta-llama/llama-3.2-3b-instruct:free", "name": "Llama 3.2 3B Instruct (Free)"},
            {"id": "qwen/qwen3-4b:free", "name": "Qwen 3 4B (Free)"},
            {"id": "mistralai/mistral-7b-instruct:free", "name": "Mistral 7B Instruct (Free)"},
            {"id": "google/gemma-2-9b-it:free", "name": "Gemma 2 9B IT (Free)"},
            {"id": "google/gemma-3-27b-it:free", "name": "Gemma 3 27B IT (Free)"},
            # Anthropic models via OpenRouter
            {"id": "anthropic/claude-opus-4-1-20250805", "name": "Claude Opus 4.1 (OpenRouter)"},
            {"id": "anthropic/claude-opus-4-20250514", "name": "Claude Opus 4 (OpenRouter)"},
            {"id": "anthropic/claude-sonnet-4-20250514", "name": "Claude Sonnet 4 (OpenRouter)"},
            {"id": "anthropic/claude-3-7-sonnet-20250219", "name": "Claude Sonnet 3.7 (OpenRouter)"},
            {"id": "anthropic/claude-3-5-haiku-20241022", "name": "Claude Haiku 3.5 (OpenRouter)"},
            # OpenAI models via OpenRouter
            {"id": "openai/gpt-5", "name": "GPT-5 (OpenRouter)"},
            {"id": "openai/gpt-4.1", "name": "GPT-4.1 (OpenRouter)"},
            {"id": "openai/gpt-4o", "name": "GPT-4o (OpenRouter)"},
            {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini (OpenRouter)"},
            {"id": "openai/gpt-4-turbo", "name": "GPT-4 Turbo (OpenRouter)"}
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
        output_dir = Path("output")
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
        output_dir = Path("output")
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
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
