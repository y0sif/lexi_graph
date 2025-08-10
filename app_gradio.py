"""
LexiGraph Gradio Web App
Transform lectures into visual knowledge graphs
"""

import gradio as gr
import os
import time
from core.pipeline import pipeline, EXAMPLE_LECTURE
from core.utils import (
    compile_dot_to_png, 
    generate_unique_filename, 
    validate_input_text,
    cleanup_old_files
)

# Global state for storing results
current_results = {
    "summary": "",
    "graph_path": "",
    "processing": False,
    "api_key": ""
}

def process_lecture(lecture_text, provider, model, api_key, progress=gr.Progress()):
    """
    Process lecture text and generate knowledge graph
    
    Args:
        lecture_text (str): Input lecture content
        provider (str): AI provider (Anthropic, OpenAI, OpenRouter)
        model (str): Model name to use
        api_key (str): API key for the selected provider
        progress: Gradio progress tracker
    
    Returns:
        tuple: (status_message, graph_image, summary_text, download_file)
    """
    global current_results
    
    # Reset results
    current_results = {"summary": "", "graph_path": "", "processing": True, "api_key": api_key}
    
    # API Key validation
    if not api_key or not api_key.strip():
        return (
            f"❌ **Error:** Please enter your {provider} API key to use the service.",
            None,
            "",
            None
        )
    
    # Validate API key format based on provider
    validation_patterns = {
        "Anthropic": "sk-ant-",
        "OpenAI": "sk-",
        "OpenRouter": "sk-or-"
    }
    
    if provider in validation_patterns:
        expected_pattern = validation_patterns[provider]
        if not api_key.startswith(expected_pattern):
            return (
                f"❌ **Error:** Invalid {provider} API key format. {provider} API keys should start with '{expected_pattern}'",
                None,
                "",
                None
            )
    
    # Set the API key as environment variable for the pipeline
    # Map providers to environment variable names
    env_var_map = {
        "Anthropic": "ANTHROPIC_API_KEY",
        "OpenAI": "OPENAI_API_KEY", 
        "OpenRouter": "OPENROUTER_API_KEY"
    }
    
    os.environ[env_var_map[provider]] = api_key
    
    # Also set the model information for the pipeline
    os.environ["LLM_PROVIDER"] = provider.lower()
    os.environ["LLM_MODEL"] = model
    
    # Input validation
    if not lecture_text or not lecture_text.strip():
        return (
            "❌ **Error:** Please enter some lecture content to process.",
            None,
            "",
            None
        )
    
    is_valid, error_message = validate_input_text(lecture_text)
    if not is_valid:
        return (
            f"❌ **Input Error:** {error_message}",
            None,
            "",
            None
        )
    
    try:
        # Clean up old files
        cleanup_old_files()
        
        # Progress tracking with Gradio
        progress(0.1, desc="🔍 Validating content type...")
        
        def progress_callback(stage, message):
            if stage == "validating":
                progress(0.2, desc="🔍 Validation agent checking content...")
            elif stage == "analyzing":
                progress(0.5, desc="📝 Summarization agent analyzing content...")
            elif stage == "generating":
                progress(0.8, desc="🎨 Visualization agent creating graph...")
        
        # Process the lecture through the pipeline
        summary, dot_code = pipeline(lecture_text, progress_callback)
        
        # Check if processing failed
        if dot_code is None:
            current_results["processing"] = False
            
            # Handle different types of errors
            if "Invalid content type detected" in summary:
                error_msg = f"❌ **Content Validation Failed:** {summary}\n\n💡 **Tip:** Please provide educational content such as:\n- Academic lectures or presentations\n- Tutorial or course materials\n- Technical documentation\n- Informational articles with learning value"
            elif "Connection refused" in summary or "API" in summary:
                error_msg = f"❌ **Connection Error:** Check your {provider} API key and model selection\n\nError details: {summary}"
            else:
                error_msg = f"❌ **Processing Error:** {summary}"
            
            return (error_msg, None, "", None)
        
        progress(0.9, desc="🖼️ Rendering visual graph...")
        
        # Generate unique filename and compile to PNG
        output_filename = generate_unique_filename()
        graph_path = compile_dot_to_png(dot_code, output_filename)
        
        if graph_path and os.path.exists(graph_path):
            # Update global results
            current_results["summary"] = summary
            current_results["graph_path"] = graph_path
            current_results["processing"] = False
            
            progress(1.0, desc="✅ Knowledge graph ready!")
            
            success_msg = "🎉 **Success!** Your knowledge graph has been generated successfully!"
            
            return (
                success_msg,
                graph_path,  # This will display the image
                summary,     # This will show in the summary textbox
                graph_path   # This will be available for download
            )
        else:
            current_results["processing"] = False
            return (
                "❌ **Rendering Error:** Failed to render graph - Please contact support",
                None,
                "",
                None
            )
            
    except Exception as e:
        current_results["processing"] = False
        return (
            f"❌ **Unexpected Error:** {str(e)}",
            None,
            "",
            None
        )

def load_example():
    """Load example lecture content"""
    return EXAMPLE_LECTURE

def clear_all():
    """Clear all inputs and outputs"""
    global current_results
    current_results = {"summary": "", "graph_path": "", "processing": False, "api_key": ""}
    return "", "", None, "", None

def update_models_and_placeholder(provider):
    """Update available models and API key placeholder based on provider"""
    model_choices = {
        "Anthropic": [
            "claude-3-5-haiku-20241022",
            "claude-3-5-sonnet-20241022", 
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229"
        ],
        "OpenAI": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo"
        ],
        "OpenRouter": [
            # Free models
            "google/gemma-2-9b-it:free",
            "microsoft/phi-3-medium-128k-instruct:free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "meta-llama/llama-3.2-3b-instruct:free",
            "qwen/qwen-2-7b-instruct:free",
            "huggingfaceh4/zephyr-7b-beta:free",
            # Premium models
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3.5-haiku",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "meta-llama/llama-3.1-405b-instruct",
            "google/gemini-pro-1.5",
            "x-ai/grok-beta",
            "deepseek/deepseek-chat"
        ]
    }
    
    placeholders = {
        "Anthropic": "sk-ant-...",
        "OpenAI": "sk-...",
        "OpenRouter": "sk-or-..."
    }
    
    infos = {
        "Anthropic": "Get your API key from https://console.anthropic.com/",
        "OpenAI": "Get your API key from https://platform.openai.com/api-keys",
        "OpenRouter": "Get your API key from https://openrouter.ai/keys (Free models available!)"
    }
    
    return (
        gr.Dropdown(choices=model_choices[provider], value=model_choices[provider][0]),
        gr.Textbox(placeholder=placeholders[provider], label=f"🔑 {provider} API Key", info=infos[provider])
    )

def validate_api_key_universal(api_key, provider):
    """Validate API key based on provider"""
    if not api_key or not api_key.strip():
        return f"ℹ️ Please enter your {provider} API key to use the service."
    
    validation_patterns = {
        "Anthropic": ("sk-ant-", "Anthropic API keys should start with 'sk-ant-'"),
        "OpenAI": ("sk-", "OpenAI API keys should start with 'sk-'"),
        "OpenRouter": ("sk-or-", "OpenRouter API keys should start with 'sk-or-'")
    }
    
    if provider in validation_patterns:
        pattern, message = validation_patterns[provider]
        if not api_key.startswith(pattern):
            return f"⚠️ {message} Please check your key."
    
    return f"✅ {provider} API key format looks correct!"

# Custom CSS for better styling
custom_css = """
/* Modern, clean styling with good readability */
.gradio-container {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

/* Main content area with modern card design */
.gradio-container .gr-block {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.18);
    margin: 1rem;
    padding: 2rem;
}

/* Clean text styling */
.gradio-container {
    color: #2d3748;
    line-height: 1.6;
}

.gradio-container h1, .gradio-container h2, .gradio-container h3, 
.gradio-container h4, .gradio-container h5, .gradio-container h6 {
    color: #1a202c !important;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.gradio-container p {
    color: #2d3748 !important;
    margin-bottom: 1rem;
}

.gradio-container label {
    color: #1a202c !important;
    font-weight: 500 !important;
    font-size: 0.95rem;
}

/* Info text styling */
.gradio-container .gr-form .gr-box .gr-padded .gr-text-sm {
    color: #4a5568 !important;
}

.gradio-container .gr-form .gr-box .gr-padded .gr-text-sm a {
    color: #667eea !important;
    font-weight: 500 !important;
}

/* Modern input styling */
.gradio-container textarea, 
.gradio-container input {
    background: #ffffff !important;
    border: 2px solid #e2e8f0 !important;
    border-radius: 12px !important;
    color: #2d3748 !important;
    font-size: 0.95rem;
    padding: 12px 16px !important;
    transition: all 0.2s ease;
}

.gradio-container textarea:focus, 
.gradio-container input:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    outline: none !important;
}

/* Modern button styling */
.gradio-container button {
    border-radius: 12px !important;
    font-weight: 500 !important;
    padding: 12px 24px !important;
    transition: all 0.2s ease !important;
    border: none !important;
    font-size: 0.95rem !important;
}

.gradio-container .gr-button-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: #ffffff !important;
}

.gradio-container .gr-button-primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3) !important;
}

.gradio-container .gr-button-secondary {
    background: #f7fafc !important;
    color: #4a5568 !important;
    border: 2px solid #e2e8f0 !important;
}

.gradio-container .gr-button-secondary:hover {
    background: #edf2f7 !important;
    border-color: #cbd5e0 !important;
}

/* Header styling */
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    font-size: 3rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    letter-spacing: -0.02em;
}

.subtitle {
    text-align: center;
    color: #718096;
    font-size: 1.25rem;
    margin-bottom: 2rem;
    font-weight: 400;
}

/* Modern info boxes */
.info-box {
    background: linear-gradient(135deg, #e6fffa 0%, #f0fff4 100%);
    border: 1px solid #9ae6b4;
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1.5rem 0;
    color: #2d3748;
}

.warning-box {
    background: linear-gradient(135deg, #ffffff 0%, #fefefe 100%);
    border: 2px solid #f6ad55;
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1.5rem 0;
    color: #2d3748;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.warning-box p {
    color: #2d3748 !important;
    margin-bottom: 0.75rem;
}

.warning-box strong {
    color: #1a202c !important;
}

.warning-box small {
    color: #4a5568 !important;
}

/* Modern cards for side panels */
.info-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    border: 2px solid #e2e8f0;
}

.info-card h4 {
    color: #1a202c !important;
    margin-bottom: 1rem;
    font-size: 1.1rem;
    font-weight: 600;
}

.info-card p {
    color: #2d3748 !important;
    margin-bottom: 0.75rem;
}

.info-card ul {
    list-style: none;
    padding: 0;
}

.info-card li {
    color: #2d3748 !important;
    margin-bottom: 0.5rem;
    padding-left: 1.5rem;
    position: relative;
}

.info-card li:before {
    content: "•";
    color: #667eea;
    font-weight: bold;
    position: absolute;
    left: 0;
}

.info-card strong {
    color: #1a202c !important;
}

/* Status messages */
.status-success {
    background: linear-gradient(135deg, #ffffff 0%, #f0fff4 100%);
    border-left: 4px solid #48bb78;
    color: #1a202c !important;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    margin: 1rem 0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.status-error {
    background: linear-gradient(135deg, #ffffff 0%, #fed7d7 100%);
    border-left: 4px solid #f56565;
    color: #1a202c !important;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    margin: 1rem 0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Image container */
.gradio-container .gr-image {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

/* Links */
.gradio-container a {
    color: #667eea;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s ease;
}

.gradio-container a:hover {
    color: #5a67d8;
    text-decoration: underline;
}

/* Remove forced colors that might conflict */
.gradio-container * {
    color: inherit;
}
"""

# Create the Gradio interface
def create_interface():
    with gr.Blocks(css=custom_css, title="LexiGraph - Lecture to Knowledge Graph", theme=gr.themes.Soft()) as app:
        
        # Header
        gr.HTML("""
            <div class="main-header">🔗 LexiGraph</div>
            <div class="subtitle">Transform lectures into visual knowledge graphs</div>
        """)
        
        # API Configuration info
        gr.HTML("""
            <div class="info-box">
                🆓 <strong>Free AI Models Available!</strong> OpenRouter provides access to free models like Gemma, Llama, and Phi-3. Select your preferred AI provider and model, then enter your API key.
            </div>
        """)
        
        # LLM Configuration Section
        with gr.Row():
            with gr.Column(scale=3):
                # Provider selection
                provider_dropdown = gr.Dropdown(
                    label="🤖 AI Provider",
                    choices=["OpenRouter", "Anthropic", "OpenAI"],
                    value="OpenRouter",
                    info="Choose your preferred AI provider (OpenRouter has free models!)"
                )
                
                # Model selection (will be updated based on provider)
                model_dropdown = gr.Dropdown(
                    label="🧠 Model",
                    choices=[
                        "google/gemma-2-9b-it:free",
                        "microsoft/phi-3-medium-128k-instruct:free",
                        "meta-llama/llama-3.1-8b-instruct:free",
                        "meta-llama/llama-3.2-3b-instruct:free",
                        "qwen/qwen-2-7b-instruct:free",
                        "huggingfaceh4/zephyr-7b-beta:free",
                        "anthropic/claude-3.5-sonnet",
                        "anthropic/claude-3.5-haiku",
                        "openai/gpt-4o",
                        "openai/gpt-4o-mini",
                        "meta-llama/llama-3.1-405b-instruct",
                        "google/gemini-pro-1.5",
                        "x-ai/grok-beta",
                        "deepseek/deepseek-chat"
                    ],
                    value="google/gemma-2-9b-it:free",
                    info="Select the AI model for knowledge graph generation (Free models available!)"
                )
                
                # API Key input (placeholder will update based on provider)
                api_key_input = gr.Textbox(
                    label="🔑 OpenRouter API Key",
                    placeholder="sk-or-...",
                    type="password",
                    info="Get your API key from https://openrouter.ai/keys (Free models available!)"
                )
                
                api_key_status = gr.HTML(value="ℹ️ Please configure your AI provider and enter your API key.")
            
            with gr.Column(scale=1):
                provider_info = gr.HTML("""
                    <div class="warning-box">
                        <p><strong style="color: #1a202c !important;">🔗 Get API Keys:</strong></p>
                        <p><a href="https://openrouter.ai/keys" target="_blank" style="color: #667eea !important; font-weight: 500;">🆓 OpenRouter (Free Models!)</a></p>
                        <p><a href="https://console.anthropic.com/" target="_blank" style="color: #667eea !important; font-weight: 500;">Anthropic Console</a></p>
                        <p><a href="https://platform.openai.com/api-keys" target="_blank" style="color: #667eea !important; font-weight: 500;">OpenAI Platform</a></p>
                        <p><small style="color: #4a5568 !important;">OpenRouter offers free access to Gemma, Llama, Phi-3 & more!</small></p>
                    </div>
                """)
        
        gr.HTML("<hr>")
        
        # Main interface
        with gr.Row():
            with gr.Column(scale=3):
                lecture_input = gr.Textbox(
                    label="📝 Enter Your Lecture Content",
                    placeholder="Enter your lecture notes, slides, or any educational content...",
                    lines=12,
                    max_lines=20
                )
                
                with gr.Row():
                    generate_btn = gr.Button("🚀 Generate Knowledge Graph", variant="primary", scale=2)
                    example_btn = gr.Button("📚 Try Example Lecture", variant="secondary", scale=1)
                    clear_btn = gr.Button("🧹 Clear All", variant="stop", scale=1)
            
            with gr.Column(scale=1):
                gr.HTML("""
                    <div class="info-card">
                        <h4>🤖 AI Agents</h4>
                        <p><strong>Three specialized agents:</strong></p>
                        <ul>
                            <li>🔍 <strong>Validation Agent</strong> - Content type checking</li>
                            <li>📝 <strong>Summarization Agent</strong> - Structure analysis</li>
                            <li>🎨 <strong>Visualization Agent</strong> - Graph generation</li>
                        </ul>
                        
                        <h4>💡 Tips</h4>
                        <ul>
                            <li>Use clear, structured content</li>
                            <li>Include main topics and subtopics</li>
                            <li>The longer the content, the richer the graph</li>
                        </ul>
                        
                        <h4>🛠️ Requirements</h4>
                        <ul>
                            <li><strong>AI Provider:</strong> OpenRouter (free models!), Anthropic, or OpenAI</li>
                            <li><strong>API Key:</strong> From your chosen provider</li>
                            <li><strong>Internet connection</strong> for API access</li>
                        </ul>
                        
                        <h4>🎯 Supported Models</h4>
                        <ul>
                            <li><strong>🆓 OpenRouter Free:</strong> Gemma-2, Llama-3.1/3.2, Phi-3, Qwen-2, Zephyr</li>
                            <li><strong>OpenRouter Premium:</strong> Claude, GPT-4o, Llama-405B, Gemini, Grok</li>
                            <li><strong>Anthropic:</strong> Claude 3.5 Haiku/Sonnet, Claude 3 Opus</li>
                            <li><strong>OpenAI:</strong> GPT-4o, GPT-4 Turbo, GPT-3.5</li>
                        </ul>
                    </div>
                """)
        
        # Results section
        gr.HTML("<hr>")
        
        status_output = gr.HTML(label="Status")
        
        with gr.Row():
            with gr.Column(scale=2):
                graph_output = gr.Image(
                    label="🎨 Generated Knowledge Graph",
                    show_label=True,
                    show_download_button=True,
                    container=True
                )
            
            with gr.Column(scale=1):
                summary_output = gr.Textbox(
                    label="📋 Generated Summary",
                    lines=10,
                    max_lines=15,
                    show_copy_button=True
                )
        
        # Download section
        download_file = gr.File(
            label="⬇️ Download Knowledge Graph",
            visible=True
        )
        
        # Event handlers
        provider_dropdown.change(
            fn=update_models_and_placeholder,
            inputs=[provider_dropdown],
            outputs=[model_dropdown, api_key_input]
        )
        
        api_key_input.change(
            fn=validate_api_key_universal,
            inputs=[api_key_input, provider_dropdown],
            outputs=[api_key_status]
        )
        
        generate_btn.click(
            fn=process_lecture,
            inputs=[lecture_input, provider_dropdown, model_dropdown, api_key_input],
            outputs=[status_output, graph_output, summary_output, download_file],
            show_progress=True
        )
        
        example_btn.click(
            fn=load_example,
            outputs=[lecture_input]
        )
        
        clear_btn.click(
            fn=clear_all,
            outputs=[lecture_input, api_key_input, graph_output, summary_output, download_file]
        )
        
    return app

def main():
    """Main function to launch the Gradio app"""
    app = create_interface()
    
    # Launch the app
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True,
        quiet=False
    )

if __name__ == "__main__":
    main()
